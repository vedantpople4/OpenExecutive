def _submit(client, prompt, agents=None, team_mode_enabled=False, parent_run_id=None):
    body = {"prompt": prompt, "agents": agents or ["ceo"], "teamModeEnabled": team_mode_enabled}
    if parent_run_id is not None:
        body["parentRunId"] = parent_run_id
    return client.post("/decisions", json=body)


def test_submit_and_get_decision_roundtrip(client):
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
