"""End-to-end smoke test against a *running* backend (real HTTP, not
TestClient/moto) — exercises all 10 endpoints from Section 1 of the plan in
sequence, sharing state (a real created decision) across checks. Complements
the pytest suite rather than replacing it: pytest verifies logic in-process
per endpoint, this verifies the actual wire format against a live server.

Usage:
    python -m scripts.smoke_test [--base-url http://localhost:8000]

Needs a server already running against some DynamoDB (real, dynamodb-local,
or moto_server) with tables created — see README section below or run:
    docker compose up -d                              # real dynamodb-local
    DYNAMODB_ENDPOINT_URL=http://localhost:8000 python -m scripts.create_tables
    uvicorn app.main:app --port 8000
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Results:
    passed: int = 0
    failed: list[str] = field(default_factory=list)

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
            print(f"  PASS  {name}")
        else:
            self.failed.append(name)
            print(f"  FAIL  {name}  {detail}")


def request(
    base_url: str, method: str, path: str, body: dict[str, Any] | None = None
) -> tuple[int, Any]:
    url = f"{base_url}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = response.read()
            return response.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw.decode(errors="replace")


def run(base_url: str) -> Results:
    r = Results()

    print("-- static config --")
    status, body = request(base_url, "GET", "/health")
    r.check("GET /health -> 200 ok", status == 200 and body == {"status": "ok"}, f"got {status} {body}")

    status, body = request(base_url, "GET", "/agents")
    r.check(
        "GET /agents -> 4 CXOs",
        status == 200 and isinstance(body, list) and {a["name"] for a in body} == {"ceo", "cfo", "cto", "cmo"},
        f"got {status} {body}",
    )

    status, body = request(base_url, "GET", "/teams")
    r.check(
        "GET /teams -> 4 keys",
        status == 200 and isinstance(body, dict) and set(body.keys()) == {"ceo", "cfo", "cto", "cmo"},
        f"got {status} {body}",
    )

    status, body = request(base_url, "GET", "/agents/ceo/prompt")
    r.check(
        "GET /agents/ceo/prompt -> non-empty",
        status == 200 and isinstance(body, dict) and len(body.get("prompt", "")) > 0,
        f"got {status} {body}",
    )

    status, _ = request(base_url, "GET", "/agents/not-a-real-agent/prompt")
    r.check("GET /agents/{unknown}/prompt -> 404", status == 404, f"got {status}")

    print("-- decisions --")
    status, body = request(
        base_url,
        "POST",
        "/decisions",
        {"prompt": "[smoke_test] Should we open an office in Berlin?", "agents": ["ceo", "cfo"], "teamModeEnabled": False},
    )
    run_id = body.get("runId") if isinstance(body, dict) else None
    r.check("POST /decisions -> 202 with runId", status == 202 and bool(run_id), f"got {status} {body}")

    status, body = request(base_url, "GET", f"/decisions/{run_id}")
    r.check(
        "GET /decisions/{id} -> matches submitted prompt",
        status == 200 and isinstance(body, dict) and body.get("prompt", "").startswith("[smoke_test]"),
        f"got {status} {body}",
    )

    status, _ = request(base_url, "GET", "/decisions/does-not-exist")
    r.check("GET /decisions/{unknown} -> 404", status == 404, f"got {status}")

    status, body = request(base_url, "GET", "/decisions")
    r.check(
        "GET /decisions -> includes the new run",
        status == 200 and isinstance(body, dict) and any(item["runId"] == run_id for item in body.get("items", [])),
        f"got {status} {body}",
    )

    status, body = request(
        base_url,
        "POST",
        "/decisions",
        {"prompt": "[smoke_test] Follow-up", "agents": ["ceo"], "teamModeEnabled": False, "parentRunId": run_id},
    )
    child_run_id = body.get("runId") if isinstance(body, dict) else None
    r.check("POST /decisions with valid parentRunId -> 202", status == 202 and bool(child_run_id), f"got {status} {body}")

    status, _ = request(
        base_url,
        "POST",
        "/decisions",
        {"prompt": "orphan", "agents": ["ceo"], "teamModeEnabled": False, "parentRunId": "does-not-exist"},
    )
    r.check("POST /decisions with unknown parentRunId -> 404", status == 404, f"got {status}")

    print("-- stop --")
    status, body = request(base_url, "POST", f"/decisions/{run_id}/stop")
    r.check("POST /decisions/{id}/stop -> stopped", status == 200 and body == {"status": "stopped"}, f"got {status} {body}")

    status, body = request(base_url, "POST", f"/decisions/{run_id}/stop")
    r.check("POST /decisions/{id}/stop again -> idempotent", status == 200 and body == {"status": "stopped"}, f"got {status} {body}")

    status, _ = request(base_url, "POST", "/decisions/does-not-exist/stop")
    r.check("POST /decisions/{unknown}/stop -> 404", status == 404, f"got {status}")

    print("-- compare --")
    status, body = request(base_url, "GET", f"/compare?old={run_id}&new={run_id}")
    r.check(
        "GET /compare (same run twice) -> no diff",
        status == 200 and isinstance(body, dict) and body.get("same_prompt") is True and body.get("consensus_added") == [],
        f"got {status} {body}",
    )

    status, _ = request(base_url, "GET", "/compare?old=does-not-exist&new=also-missing")
    r.check("GET /compare with unknown ids -> 404", status == 404, f"got {status}")

    print("-- dashboard --")
    status, body = request(base_url, "GET", "/dashboard")
    r.check(
        "GET /dashboard -> counts the smoke-test runs",
        status == 200 and isinstance(body, dict) and body.get("total_decisions", 0) >= 2,
        f"got {status} {body}",
    )

    print("-- events (SSE) --")
    status, _ = request(base_url, "GET", "/decisions/does-not-exist/events")
    r.check("GET /decisions/{unknown}/events -> 404", status == 404, f"got {status}")

    # run_id is stopped (terminal), so this replays-and-closes rather than
    # hanging on a live tail — safe to read the full body with a plain GET.
    status, body = request(base_url, "GET", f"/decisions/{run_id}/events")
    r.check("GET /decisions/{id}/events (terminal) -> 200", status == 200, f"got {status} {body}")

    return r


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    print(f"Smoke-testing {args.base_url}\n")
    results = run(args.base_url)

    print(f"\n{results.passed} passed, {len(results.failed)} failed")
    if results.failed:
        print("Failed checks:", ", ".join(results.failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
