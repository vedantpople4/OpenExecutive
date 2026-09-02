# Deploying OpenExec to Oracle Cloud

One Always Free ARM instance, two containers: nginx serves the SPA and proxies
`/api` to the FastAPI service. Cloudflare provides DNS and TLS. Supabase
provides Postgres. Total cost: nothing.

## Before you start

| You need | Notes |
|---|---|
| Oracle Cloud account | Always Free tier; card required for identity only |
| A domain | Cloudflare gives DNS + TLS free, but does not sell you a hostname |
| Supabase project | Free plan |
| An OpenAI-compatible LLM endpoint | LM Studio on `127.0.0.1:1234` will not exist on the server — have a provider's `base_url`, `model`, and `api_key` ready |

The LLM provider is the only thing here that costs money.

---

## 1. Instance

Create a VM with shape **`VM.Standard.A1.Flex`** (Ampere, ARM64), **2 OCPUs and
12 GB memory** — the whole Always Free ARM allowance (1,500 OCPU-hours and
9,000 GB-hours per month) in one instance. Ubuntu 22.04 or Oracle Linux 9 both
work.

Do not use the `E2.1.Micro` AMD shape. It has 1 GB of memory and the Vite build
will OOM.

**On ARM:** both base images (`python:3.12-slim`, `node:22-alpine`) are
multi-arch, so building on the box just works. Nothing in the Dockerfiles needs
to change. Building elsewhere and pushing does — you would need
`docker buildx --platform linux/arm64`.

## 2. Convert the account to Pay As You Go — do this before anything else

Oracle reclaims an Always Free compute instance after a 7-day period in which
the 95th-percentile CPU is under 20%, network is under 20%, **and** memory is
under 20% (the memory condition applies to A1 shapes).

OpenExec idles well under all three. nginx and one uvicorn worker use a few
hundred MB of 12 GB — roughly 4% — and the box is silent between deliberations.
Left on Always Free, this instance is a candidate for reclamation.

Converting to Pay As You Go exempts instances from reclamation, and you are
still charged nothing as long as usage stays inside the Always Free limits.

This is the single most likely way to lose a working deployment, and it fails
silently a week after you stop paying attention.

## 3. Networking

If you use Cloudflare Tunnel (step 6, recommended), **skip this entirely** — no
inbound ports are needed.

Otherwise open port 80 in the subnet's Security List, and then open it *again*
on the instance itself. Oracle's images ship with a local firewall that blocks
everything except SSH, so a correct Security List alone still gives a hanging
connection with no error:

```bash
# Ubuntu
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo netfilter-persistent save

# Oracle Linux
sudo firewall-cmd --permanent --add-port=80/tcp && sudo firewall-cmd --reload
```

Never open 8000. The API publishes no host port; nginx reaches it over the
compose network.

## 4. Docker and code

```bash
# Ubuntu
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker      # --now so it survives a reboot
sudo usermod -aG docker $USER           # log out and back in

git clone https://github.com/vedantpople4/OpenExecutive.git /opt/openexec
cd /opt/openexec
```

Write the LLM configuration. **This file is gitignored and excluded from the
Docker build context — create it on the host, never commit it:**

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

## 5. Database — Supabase

Create a project, then take the connection string from **Connect → Session
pooler**, not the direct connection.

This matters and the failure is confusing. Supabase's direct connection on port
5432 is **IPv6-only** unless the project buys the IPv4 add-on, and an Oracle
instance is IPv4 by default — so the direct string fails to connect with
nothing useful in the logs. Supavisor **session mode** is IPv4 on every tier,
and session mode (not transaction mode, port 6543, which is built for
serverless) is what a long-lived server wants.

```bash
echo 'DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres' \
  | sudo tee -a /opt/openexec/.env
```

Then create the schema:

```bash
docker compose run --rm api python -m scripts.create_tables
```

## 6. Expose it — Cloudflare Tunnel

Recommended over a DNS A record because it needs no open ports, so step 3
disappears along with the firewall problem, and your origin IP stays unlisted.

**A tunnel needs a domain whose nameservers you control.** It works with a
domain you own or a delegated one (`eu.org`); it does *not* work with a free
subdomain like `is-a.dev`, because the record lives in someone else's
Cloudflare zone and a tunnel route can only be created inside your own. On a
free subdomain, use the A-record path below instead.

In the Cloudflare dashboard: **Zero Trust → Networks → Tunnels → Create**, then
route your hostname to `http://web:80`. Copy the connector token:

```bash
echo 'CLOUDFLARE_TUNNEL_TOKEN=eyJ...' | sudo tee -a /opt/openexec/.env
docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml up -d
```

<details>
<summary>Alternative: DNS A record</summary>

Complete step 3, then point an `A` record at the instance's public IP with
the proxy enabled.

**On your own Cloudflare zone:** enable the orange cloud, set **SSL/TLS → Full
(strict)**, and install a Cloudflare Origin Certificate on nginx. That needs a
TLS server block `deploy/nginx.conf` does not currently have. "Flexible" mode
skips that work but leaves Cloudflare-to-origin traffic in plaintext across
the internet.

**On a free subdomain such as `is-a.dev`:** set `"proxied": true` in your
registration JSON — their `dnsconfig.js` maps it to `CF_PROXY_ON`, so you get
Cloudflare-terminated TLS on an origin still serving plain `:80`. You do not
control that zone's SSL mode, so Full (strict) is not available to you; the
origin hop is plaintext. Fine for a demo, not for real data.

</details>

## 7. Start

```bash
docker compose up -d --build
```

## 8. Verify

```bash
# Resolved config path and whether the mount landed
curl -s https://<your-domain>/api/health
# -> {"status":"ok","settings_path":"/etc/openexec/settings.json","settings_found":true}

# Exactly one uvicorn worker (see below)
docker compose exec api ps ax | grep uvicorn

docker compose logs -f api
```

`settings_found: false` means the mount failed. With
`OPENEXEC_REQUIRE_SETTINGS=1` the container should have refused to boot
instead, so if you see this, check that variable is still set.

Then open `https://<your-domain>/` and submit a decision. A full deliberation
is 5–26 sequential LLM calls, roughly 5–10 minutes.

---

## Operating notes

**One worker, deliberately.** Live SSE fan-out (`app/services/event_bus.py`)
keeps subscribers in a module-level dict, and `app/services/orchestration.py`
holds the run lock, the cancellation registry, and the captured event loop in
process globals. A second worker would let a browser connect to a process that
is not running the deliberation and watch an empty stream while the run
proceeds invisibly elsewhere. Scaling out requires moving that fan-out to a
shared broker first — and it is also what stops this app from running on any
serverless platform.

**One deliberation at a time.** `_run_lock` serialises runs process-wide, so a
second submission queues behind the first for its full 5–10 minutes.

**The SSE stream sends a keepalive every 30s.** Cloudflare closes a proxied
connection idle for 100 seconds with a 524, and that ceiling is not adjustable
below Enterprise. Since the gap between two events is just an LLM call running
long, `app/routers/events.py` emits an SSE comment frame during quiet
stretches. If you put a different proxy in front, check its idle timeout
against `_HEARTBEAT_SECONDS`.

**Updating:**

```bash
cd /opt/openexec && git pull && docker compose up -d --build
```

**Bind-mount gotcha:** if `/etc/openexec/settings.json` does not exist, Docker
creates a *directory* at that path rather than failing. The API then
crash-loops on the settings probe — correct behaviour, but delete the stray
directory before writing the real file.

## Local development

Same images, plus a disposable Postgres instead of Supabase:

```bash
cp .env.example .env       # set OPENEXEC_SETTINGS_FILE=./settings.json
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.local.yml \
  run --rm api python -m scripts.create_tables
```

The app is on `http://localhost/`; Postgres is on host port 5433 (5432 is left
free for a Homebrew instance already running on the same machine).
