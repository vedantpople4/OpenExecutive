from app.repositories import decisions as repo
from app.services import orchestration


def _submit(client, prompt, agents=None, team_mode_enabled=False, parent_run_id=None):
    body = {"prompt": prompt, "agents": agents or ["ceo"], "teamModeEnabled": team_mode_enabled}
    if parent_run_id is not None:
        body["parentRunId"] = parent_run_id
    return client.post("/decisions", json=body)


def test_submit_and_get_decision_roundtrip(client, monkeypatch):
    # TestClient runs BackgroundTasks synchronously to completion before
    # client.post() returns, so without this the real orchestrator would run
    # (and finish, since these tests have no settings.json) before the
    # assertions below even execute. This test's job is create+read wiring,
    # not orchestration -- see test_orchestration.py for that.
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)

    response = _submit(client, "Should we launch in APAC?", agents=["ceo", "cfo"])
    assert response.status_code == 202
    run_id = response.json()["runId"]
    assert run_id.startswith("run-")

    detail = client.get(f"/decisions/{run_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["runId"] == run_id
    assert body["prompt"] == "Should we launch in APAC?"
    assert body["board_decision"] == {
        "consensus_points": [],
        "dissent_points": [],
        "final_priority_actions": [],
        "dissenting_opinions": [],
        "contingencies": [],
        "summary": None,
        "status": None,
    }
    assert body["agent_reports"] == {}
    assert body["action_items"] == []


def test_detail_exposes_error_status_and_message(client, monkeypatch):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we launch in APAC?").json()["runId"]

    repo.fail_decision(run_id, "LLM provider unreachable")

    body = client.get(f"/decisions/{run_id}").json()
    assert body["status"] == "error"
    assert body["error_message"] == "LLM provider unreachable"


def test_list_exposes_status(client, monkeypatch):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we launch in APAC?").json()["runId"]

    items = client.get("/decisions").json()["items"]
    assert next(i for i in items if i["runId"] == run_id)["status"] == "running"


def test_get_decision_not_found_returns_404(client):
    response = client.get("/decisions/does-not-exist")
    assert response.status_code == 404


def test_submit_decision_with_unknown_parent_returns_404(client):
    response = _submit(client, "Follow-up", parent_run_id="does-not-exist")
    assert response.status_code == 404


def test_submit_decision_with_valid_parent_sets_has_children(client):
    root_id = _submit(client, "Root decision").json()["runId"]

    child = _submit(client, "Follow-up decision", parent_run_id=root_id)
    assert child.status_code == 202

    listing = client.get("/decisions").json()
    root_summary = next(item for item in listing["items"] if item["runId"] == root_id)
    child_summary = next(item for item in listing["items"] if item["runId"] == child.json()["runId"])
    assert root_summary["hasChildren"] is True
    assert child_summary["hasChildren"] is False
    assert child_summary["parentRunId"] == root_id


def test_list_decisions_paginates_via_cursor(client):
    ids = [_submit(client, f"Decision {i}").json()["runId"] for i in range(3)]

    page1 = client.get("/decisions", params={"limit": 2}).json()
    assert len(page1["items"]) == 2
    assert page1["nextCursor"] is not None

    page2 = client.get("/decisions", params={"limit": 2, "cursor": page1["nextCursor"]}).json()
    assert len(page2["items"]) == 1
    assert page2["nextCursor"] is None

    all_ids = [item["runId"] for item in page1["items"] + page2["items"]]
    assert set(all_ids) == set(ids)
    assert len(all_ids) == len(set(all_ids))


def test_list_decisions_substring_search(client):
    _submit(client, "Expand into APAC market")
    _submit(client, "Cut marketing budget")

    response = client.get("/decisions", params={"q": "apac"}).json()
    assert len(response["items"]) == 1
    assert "APAC" in response["items"][0]["prompt"]


def test_search_matches_beyond_the_first_page(client):
    """Search filters in SQL, before the limit.

    The DynamoDB version fetched one page and filtered it in Python
    afterwards, so a match sitting past the page boundary was invisible and
    the page came back short. This is the behaviour change that move brings.
    """
    for i in range(12):
        _submit(client, f"Routine decision {i}")
    _submit(client, "Acquire the Bratislava plant")

    # The needle is the oldest row, so a limit of 5 puts it well past the
    # first page in recency order.
    body = client.get("/decisions", params={"q": "Bratislava", "limit": 5}).json()

    assert [item["prompt"] for item in body["items"]] == ["Acquire the Bratislava plant"]


def test_search_is_case_insensitive(client):
    _submit(client, "Expand into APAC")
    body = client.get("/decisions", params={"q": "apac"}).json()
    assert len(body["items"]) == 1


def test_pagination_walks_every_row_exactly_once(client):
    """Keyset pagination over a full walk: no row repeated, none skipped."""
    for i in range(7):
        _submit(client, f"Decision {i}")

    seen, cursor = [], None
    for _ in range(10):  # generous bound; the walk should finish well inside it
        params = {"limit": 3}
        if cursor:
            params["cursor"] = cursor
        body = client.get("/decisions", params=params).json()
        seen.extend(item["runId"] for item in body["items"])
        cursor = body.get("nextCursor")
        if not cursor:
            break

    assert len(seen) == 7
    assert len(set(seen)) == 7


def test_timestamp_keeps_its_wire_format(client):
    """created_at is timestamptz in Postgres but the API has always emitted
    ISO with milliseconds and a literal Z. The frontend parses it, so the
    conversion happens in the repository rather than changing the contract."""
    import re

    run_id = _submit(client, "Check the wire format").json()["runId"]
    timestamp = client.get(f"/decisions/{run_id}").json()["timestamp"]

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", timestamp), timestamp
