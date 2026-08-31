# Deploying OpenExec to EC2

One instance, two containers: nginx serves the SPA and proxies `/api` to the
FastAPI service. DynamoDB is the only external dependency.

## Before you start

You need an OpenAI-compatible LLM endpoint reachable from the instance. The
local development setup points at LM Studio on `127.0.0.1:1234`; that will not
exist on EC2, so have a provider's `base_url`, `model`, and `api_key` ready.

**Instance size.** t2.micro (1 GB) is enough to *run* both containers but will
likely OOM while building the frontend image — the Vite/TypeScript build is the
memory-hungry step. Use t3.small or larger for the build, or build the images
elsewhere and pull them.

---

## 1. Instance and network

Launch Amazon Linux 2023. Security group inbound:

| Port | Source | Why |
|---|---|---|
| 80 | 0.0.0.0/0 | nginx |
| 22 | your IP only | SSH |

**Do not open 8000.** The API publishes no host port; nginx reaches it over the
compose network. An open 8000 would only serve to bypass the proxy.

## 2. IMDSv2 hop limit — do this before anything else

```bash
aws ec2 modify-instance-metadata-options \
  --instance-id i-xxxxxxxx \
  --http-tokens required \
  --http-put-response-hop-limit 2
```

The default hop limit of 1 stops packets from inside a container reaching the
instance metadata service, so boto3 cannot pick up the instance role and every
DynamoDB call fails with `Unable to locate credentials`. Docker adds a network
hop; 2 accounts for it.

This is the single most likely first-deploy failure, and its error message
points at credentials rather than at networking.

## 3. IAM role

Attach an instance role granting DynamoDB access to the two tables and their
indexes:

```
dynamodb:CreateTable, DescribeTable,
dynamodb:GetItem, PutItem, UpdateItem, Query, Scan
```

on `openexec-decisions`, `openexec-events`, and `openexec-decisions/index/*`.

No access keys anywhere — `docker-compose.yml` sets no `AWS_*` credential
variables precisely so the role is used.

## 4. Docker

```bash
sudo dnf install -y docker git
sudo systemctl enable --now docker      # --now so it survives a reboot
sudo usermod -aG docker ec2-user        # log out and back in
```

## 5. Code and configuration

```bash
git clone https://github.com/vedantpople4/OpenExecutive.git /opt/openexec
cd /opt/openexec
```

Write the LLM configuration. **This file is gitignored and excluded from the
Docker build context — it must be created on the host, never committed:**

```bash
sudo mkdir -p /etc/openexec
sudo tee /etc/openexec/settings.json >/dev/null <<'JSON'
{
  "ai": {
    "base_url": "https://api.your-provider.com/v1",
    "api_key": "sk-...",
    "model": "your-model",
    "temperature": 0.7,
    "max_tokens": 8192,
    "timeout": 120
  },
  "agents": { "enabled": ["ceo", "cfo", "cto", "cmo"] }
}
JSON
sudo chmod 600 /etc/openexec/settings.json
```

Optionally `cp .env.example .env` and edit — every value has a working default.

## 6. Create the DynamoDB tables

Idempotent, so it is safe to re-run. No Python needed on the host:

```bash
docker compose run --rm api python -m scripts.create_tables
```

## 7. Start

```bash
docker compose up -d --build
```

## 8. Verify

```bash
# Resolved config path and whether the mount landed
curl -s localhost/api/health
# -> {"status":"ok","settings_path":"/etc/openexec/settings.json","settings_found":true}

# Exactly one uvicorn worker (see below)
docker compose exec api ps ax | grep uvicorn

docker compose logs -f api
```

`settings_found: false` means the mount failed. With
`OPENEXEC_REQUIRE_SETTINGS=1` the container should have refused to boot
instead, so if you see this, check that `OPENEXEC_REQUIRE_SETTINGS` is still
set.

Then open `http://<public-ip>/` and submit a decision. A full deliberation is
5–26 sequential LLM calls, roughly 5–10 minutes.

---

## Operating notes

**One worker, deliberately.** Live SSE fan-out (`app/services/event_bus.py`)
keeps subscribers in a module-level dict, and `app/services/orchestration.py`
holds the run lock, the cancellation registry, and the captured event loop in
process globals. A second worker would let a browser connect to a process that
is not running the deliberation and watch an empty stream while the run
proceeds invisibly elsewhere. Scaling out requires moving that fan-out to a
shared broker first.

**One deliberation at a time.** `_run_lock` serialises runs process-wide, so a
second submission queues behind the first for its full 5–10 minutes.

**Updating:**

```bash
cd /opt/openexec && git pull && docker compose up -d --build
```

**Bind-mount gotcha:** if `/etc/openexec/settings.json` does not exist, Docker
creates a *directory* at that path rather than failing. The API then crash-loops
on the settings probe — correct behaviour, but delete the stray directory before
writing the real file.

**No TLS here.** This serves plain HTTP on port 80. For a public deployment put
it behind an ALB with an ACM certificate, or add certbot to the nginx container.

## Local development

Same images, plus dynamodb-local and dummy credentials:

```bash
cp .env.example .env       # set OPENEXEC_SETTINGS_FILE=./settings.json
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.local.yml \
  run --rm api python -m scripts.create_tables
```

The app is on `http://localhost/`; dynamodb-local is on host port 8001.
