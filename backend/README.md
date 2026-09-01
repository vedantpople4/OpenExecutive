# OpenExec Backend

FastAPI service backing the OpenExec frontend. Implements the 10 Phase-1
endpoints against DynamoDB, and runs real multi-agent LLM deliberations by
reusing the `openexec/` CLI engine as a library.

See the design docs for the full rationale: API contract and DynamoDB schema,
plus the LLM orchestration integration. For deploying the whole stack (API +
SPA behind nginx on a single host), see [`../deploy/README.md`](../deploy/README.md).

## Running the tests

```bash
cd backend
source ../venv/bin/activate
python -m pytest
```

Tests use `moto` for in-memory DynamoDB and never touch the network — the
orchestrator is monkeypatched, so no LLM is required.

## Running locally

The backend needs DynamoDB and (for real deliberations) an OpenAI-compatible
LLM endpoint.

### 1. DynamoDB

Either real AWS, or a local stand-in:

```bash
# Local, in-memory (no Docker needed)
moto_server -p 5001

# Or dynamodb-local via Docker, on host port 8001
docker compose -f ../docker-compose.yml -f ../docker-compose.local.yml \
    up -d dynamodb-local
```

Then create the tables:

```bash
cd backend
AWS_ACCESS_KEY_ID=devlocal AWS_SECRET_ACCESS_KEY=devlocal \
AWS_DEFAULT_REGION=us-east-1 DYNAMODB_ENDPOINT_URL=http://127.0.0.1:5001 \
python -m scripts.create_tables
```

### 2. LLM provider

Configured by `settings.json` **at the repo root** — the same file the CLI
uses (`base_url`, `model`, `temperature`, `max_tokens`, `timeout`). Point it
at Ollama, LM Studio, or any OpenAI-compatible endpoint.

### 3. Start the server

> **Launch from the repo root, or set `OPENEXEC_SETTINGS_PATH`.** `AIClient`
> resolves `settings.json` relative to the process working directory, so
> starting from `backend/` without that variable silently leaves every agent
> in fallback mode. On a server, set an absolute path plus
> `OPENEXEC_REQUIRE_SETTINGS=1` so a misconfiguration fails at boot instead of
> producing a full deliberation of stub reports. `GET /health` reports the
> resolved path and whether the file was found.

```bash
cd /path/to/OpenExec          # repo root
AWS_ACCESS_KEY_ID=devlocal AWS_SECRET_ACCESS_KEY=devlocal \
AWS_DEFAULT_REGION=us-east-1 DYNAMODB_ENDPOINT_URL=http://127.0.0.1:5001 \
PYTHONPATH=backend \
uvicorn app.main:app --port 8000
```

## Smoke tests

**Endpoint coverage** (fast, no LLM) — exercises all 10 endpoints over real
HTTP against a running server:

```bash
cd backend && python -m scripts.smoke_test
```

`postman_collection.json` covers the same surface for Postman/Insomnia/Bruno.

**Live deliberation** (slow, needs a real LLM) — proves the whole orchestration
path: background task, live SSE, and result persistence.

```bash
# 1. Submit a decision
curl -s -X POST http://localhost:8000/decisions \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Should we open an office in Berlin?","agents":["ceo","cfo"],"teamModeEnabled":false}'
# -> {"runId":"run-..."}

# 2. Watch events stream live (5-10 min for a full run)
curl -N http://localhost:8000/decisions/<runId>/events

# 3. Confirm the result persisted
curl -s http://localhost:8000/decisions/<runId>
```

A healthy run emits `simulation_initialized` through `synthesis_completed`
(the terminal event), and leaves the decision at `status="completed"` with
populated `agent_reports`, `deliberation_rounds`, and `board_decision`.
Ending on `error_occurred` instead means the run failed — the decision is
marked `status="error"` with an `error_message`.

## Notes

- A full deliberation is 5–26 sequential blocking LLM calls (~5–10 min), so it
  runs as a background task, and runs are serialized process-wide by a lock.
- Anything written to DynamoDB must go through `app/db.py`'s
  `to_dynamodb_safe()` — boto3 rejects both Python floats and non-string map
  keys, and orchestration output contains both.

### Stopping a run

`POST /decisions/{id}/stop` is **cooperative, not immediate**. The engine makes
blocking `requests` calls with no interrupt handle, so a stop is only noticed
*between* LLM calls:

| Case | Latency |
|---|---|
| Typical | 10–60s |
| One provider timeout | up to ~120s |
| Endpoint hanging through both retries, two calls in flight | ~12 min |

The UI does not wait for any of this — the stop button aborts the local stream
immediately, so the run stops looking live right away regardless.

A stopped run keeps `status="stopped"` **and** whatever partial results it had
produced. So **never infer completeness from field presence**: a decision can
carry agent reports and deliberation rounds while having no board decision at
all. The frontend keys off the board decision's presence for exactly this
reason (`projectDecisionDetailToCards.ts`).
