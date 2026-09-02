# OpenExec Backend

FastAPI service backing the OpenExec frontend. Implements the 10 Phase-1
endpoints against Postgres, and runs real multi-agent LLM deliberations by
reusing the `openexec/` CLI engine as a library.

See the design docs for the full rationale: API contract and database schema,
plus the LLM orchestration integration. For deploying the whole stack (API +
SPA behind nginx on a single host), see [`../deploy/README.md`](../deploy/README.md).

## Running the tests

```bash
cd backend
source ../venv/bin/activate
python -m pytest
```

Tests run against a real Postgres and never touch the network — the
orchestrator is monkeypatched, so no LLM is required. There is no in-memory
stand-in the way `moto` stood in for DynamoDB:

```bash
brew services start postgresql@16 && createdb openexec_test
```

Override the target with `DATABASE_URL`.

## Running locally

The backend needs Postgres and (for real deliberations) an OpenAI-compatible
LLM endpoint.

### 1. Postgres

Homebrew, or the compose override on host port 5433:

```bash
brew services start postgresql@16 && createdb openexec
# or
docker compose -f ../docker-compose.yml -f ../docker-compose.local.yml up -d postgres
```

Then apply the schema:

```bash
cd backend
DATABASE_URL=postgresql://localhost:5432/openexec python -m scripts.create_tables
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
DATABASE_URL=postgresql://localhost:5432/openexec \
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
- Result fields live in the `data` jsonb column and are flattened back to the
  top level on read, so repository callers see one flat dict. Promoting a
  field to a real column means teaching `_row_to_item` about it.

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
