"""End-to-end smoke test against a *running* backend (real HTTP, not
TestClient/moto) — exercises all 12 endpoints in sequence, sharing state (a
real created decision, and now a real signed-in session) across checks.
Complements the pytest suite rather than replacing it: pytest verifies logic
in-process per endpoint, this verifies the actual wire format against a live
server.

Usage:
    python -m scripts.smoke_test --access-token <a Supabase access token>
        [--base-url http://localhost:8000] [--origin http://localhost:5173]

Every data route now requires a session (see app/auth.py) — get an access
token by signing into the app once and copying it from the browser's network
tab (the POST /auth/session request body), or via Supabase's password grant
against your project. SUPABASE_ACCESS_TOKEN works instead of --access-token.
--origin must match a value in OPENEXEC_CORS_ORIGINS on the server, since
mutating routes now check it (verify_origin, the CSRF guard) exactly as a
real browser's request would present it.

Needs a server already running with tables created:
    DATABASE_URL=postgresql://localhost:5432/openexec python -m scripts.create_tables
    uvicorn app.main:app --port 8000
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
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


def make_opener() -> urllib.request.OpenerDirector:
    """One cookie jar for the whole run, the same way a browser tab would
    hold the session cookie POST /auth/session sets across every subsequent
    request."""
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def request(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    origin: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    url = f"{base_url}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    # Every mutating route now checks this (verify_origin, app/auth.py's CSRF
    # guard) exactly as a real browser would present it -- must match a value
    # in the server's OPENEXEC_CORS_ORIGINS.
    req.add_header("Origin", origin)
    try:
        with opener.open(req, timeout=10) as response:
            raw = response.read()
            return response.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw.decode(errors="replace")


def run(base_url: str, origin: str, access_token: str) -> Results:
    r = Results()
    opener = make_opener()

    print("-- sign in --")
    status, body = request(
        opener, base_url, origin, "POST", "/auth/session", {"access_token": access_token}
    )
    r.check("POST /auth/session -> 200 (signed in)", status == 200, f"got {status} {body}")
    if status != 200:
        print("\nCould not establish a session -- every route below needs one, aborting early.")
        return r

    print("-- static config --")
    status, body = request(opener, base_url, origin, "GET", "/health")
    r.check("GET /health -> 200 ok", status == 200 and body == {"status": "ok"}, f"got {status} {body}")

    status, body = request(opener, base_url, origin, "GET", "/agents")
    r.check(
        "GET /agents -> 4 CXOs",
        status == 200 and isinstance(body, list) and {a["name"] for a in body} == {"ceo", "cfo", "cto", "cmo"},
        f"got {status} {body}",
    )

    status, body = request(opener, base_url, origin, "GET", "/teams")
    r.check(
        "GET /teams -> 4 keys",
        status == 200 and isinstance(body, dict) and set(body.keys()) == {"ceo", "cfo", "cto", "cmo"},
        f"got {status} {body}",
    )

    status, body = request(opener, base_url, origin, "GET", "/agents/ceo/prompt")
    r.check(
        "GET /agents/ceo/prompt -> non-empty",
        status == 200 and isinstance(body, dict) and len(body.get("prompt", "")) > 0,
        f"got {status} {body}",
    )

    status, _ = request(opener, base_url, origin, "GET", "/agents/not-a-real-agent/prompt")
    r.check("GET /agents/{unknown}/prompt -> 404", status == 404, f"got {status}")

    print("-- decisions --")
    status, body = request(
        opener,
        base_url,
        origin,
        "POST",
        "/decisions",
        {"prompt": "[smoke_test] Should we open an office in Berlin?", "agents": ["ceo", "cfo"], "teamModeEnabled": False},
    )
    run_id = body.get("runId") if isinstance(body, dict) else None
    r.check("POST /decisions -> 202 with runId", status == 202 and bool(run_id), f"got {status} {body}")

    status, body = request(opener, base_url, origin, "GET", f"/decisions/{run_id}")
    r.check(
        "GET /decisions/{id} -> matches submitted prompt",
        status == 200 and isinstance(body, dict) and body.get("prompt", "").startswith("[smoke_test]"),
        f"got {status} {body}",
    )

    status, _ = request(opener, base_url, origin, "GET", "/decisions/does-not-exist")
    r.check("GET /decisions/{unknown} -> 404", status == 404, f"got {status}")

    status, body = request(opener, base_url, origin, "GET", "/decisions")
    r.check(
        "GET /decisions -> includes the new run",
        status == 200 and isinstance(body, dict) and any(item["runId"] == run_id for item in body.get("items", [])),
        f"got {status} {body}",
    )

    status, body = request(
        opener,
        base_url,
        origin,
        "POST",
        "/decisions",
        {"prompt": "[smoke_test] Follow-up", "agents": ["ceo"], "teamModeEnabled": False, "parentRunId": run_id},
    )
    child_run_id = body.get("runId") if isinstance(body, dict) else None
    r.check("POST /decisions with valid parentRunId -> 202", status == 202 and bool(child_run_id), f"got {status} {body}")

    status, _ = request(
        opener,
        base_url,
        origin,
        "POST",
        "/decisions",
        {"prompt": "orphan", "agents": ["ceo"], "teamModeEnabled": False, "parentRunId": "does-not-exist"},
    )
    r.check("POST /decisions with unknown parentRunId -> 404", status == 404, f"got {status}")

    print("-- stop --")
    status, body = request(opener, base_url, origin, "POST", f"/decisions/{run_id}/stop")
    r.check("POST /decisions/{id}/stop -> stopped", status == 200 and body == {"status": "stopped"}, f"got {status} {body}")

    status, body = request(opener, base_url, origin, "POST", f"/decisions/{run_id}/stop")
    r.check("POST /decisions/{id}/stop again -> idempotent", status == 200 and body == {"status": "stopped"}, f"got {status} {body}")

    status, _ = request(opener, base_url, origin, "POST", "/decisions/does-not-exist/stop")
    r.check("POST /decisions/{unknown}/stop -> 404", status == 404, f"got {status}")

    print("-- compare --")
    status, body = request(opener, base_url, origin, "GET", f"/compare?old={run_id}&new={run_id}")
    r.check(
        "GET /compare (same run twice) -> no diff",
        status == 200 and isinstance(body, dict) and body.get("same_prompt") is True and body.get("consensus_added") == [],
        f"got {status} {body}",
    )

    status, _ = request(opener, base_url, origin, "GET", "/compare?old=does-not-exist&new=also-missing")
    r.check("GET /compare with unknown ids -> 404", status == 404, f"got {status}")

    print("-- dashboard --")
    status, body = request(opener, base_url, origin, "GET", "/dashboard")
    r.check(
        "GET /dashboard -> counts the smoke-test runs",
        status == 200 and isinstance(body, dict) and body.get("total_decisions", 0) >= 2,
        f"got {status} {body}",
    )

    print("-- events (SSE) --")
    status, _ = request(opener, base_url, origin, "GET", "/decisions/does-not-exist/events")
    r.check("GET /decisions/{unknown}/events -> 404", status == 404, f"got {status}")

    # run_id is stopped (terminal), so this replays-and-closes rather than
    # hanging on a live tail — safe to read the full body with a plain GET.
    status, body = request(opener, base_url, origin, "GET", f"/decisions/{run_id}/events")
    r.check("GET /decisions/{id}/events (terminal) -> 200", status == 200, f"got {status} {body}")

    return r


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--origin", default="http://localhost:5173")
    parser.add_argument(
        "--access-token",
        default=os.environ.get("SUPABASE_ACCESS_TOKEN"),
        help="A Supabase access token for a signed-in test user. Also settable via "
        "SUPABASE_ACCESS_TOKEN.",
    )
    args = parser.parse_args()

    if not args.access_token:
        print(
            "No access token (--access-token or SUPABASE_ACCESS_TOKEN). Every data route "
            "now requires a session -- sign into the app once and copy the access token from "
            "the POST /auth/session request body in the browser's network tab."
        )
        return 1

    print(f"Smoke-testing {args.base_url}\n")
    results = run(args.base_url, args.origin, args.access_token)

    print(f"\n{results.passed} passed, {len(results.failed)} failed")
    if results.failed:
        print("Failed checks:", ", ".join(results.failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
