from app.db import connection
from app.repositories import decisions as decisions_repo
from app.repositories import events as events_repo
from app.services import orchestration
from tests.test_decisions import _submit


def test_delete_removes_the_decision(client, monkeypatch):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we launch in APAC?").json()["runId"]
    client.post(f"/decisions/{run_id}/stop")

    response = client.delete(f"/decisions/{run_id}")

    assert response.status_code == 204
    assert client.get(f"/decisions/{run_id}").status_code == 404


def test_delete_also_removes_the_event_timeline(client, monkeypatch):
    """The events live in a second table with no cascade and no TTL, so a
    delete that only removes the decision row leaves the whole timeline behind
    -- invisible but still stored."""
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we launch in APAC?").json()["runId"]
    events_repo.append_event(
        run_id, "2026-01-01T00:00:00Z#1", {"event_id": "1", "type": "analysis_started"}
    )
    assert events_repo.list_events(run_id) != []
    client.post(f"/decisions/{run_id}/stop")

    client.delete(f"/decisions/{run_id}")

    assert events_repo.list_events(run_id) == []


def test_delete_refuses_a_running_decision(client, monkeypatch):
    """The worker writes results back when it finishes. Deleting underneath it
    would resurrect the row minutes later, with nothing telling the caller the
    delete had been undone."""
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we launch in APAC?").json()["runId"]

    response = client.delete(f"/decisions/{run_id}")

    assert response.status_code == 409
    assert "running" in response.json()["detail"].lower()
    assert client.get(f"/decisions/{run_id}").status_code == 200


def test_delete_unknown_decision_returns_404(client):
    assert client.delete("/decisions/does-not-exist").status_code == 404


def test_delete_is_not_idempotent_and_says_so(client, monkeypatch):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we launch in APAC?").json()["runId"]
    client.post(f"/decisions/{run_id}/stop")

    assert client.delete(f"/decisions/{run_id}").status_code == 204
    assert client.delete(f"/decisions/{run_id}").status_code == 404


def test_result_writes_never_create_a_deleted_decision(client, monkeypatch):
    """_update_item is the guarded call. DynamoDB's update_item is an upsert, so
    without attribute_exists(id) any late result write conjures the row back."""
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we launch in APAC?").json()["runId"]
    client.post(f"/decisions/{run_id}/stop")
    client.delete(f"/decisions/{run_id}")

    decisions_repo._update_item(run_id, {"status": "completed"})

    assert decisions_repo.get_decision(run_id) is None


def test_a_worker_finishing_late_cannot_resurrect_a_deleted_decision(client, monkeypatch):
    """The real sequence: stop a run, delete it, and the worker's in-flight LLM
    call returns up to two minutes later and writes its partial results back.

    save_partial_decision reads the decision before writing, so the dangerous
    window is between that read and the write. This reproduces it by deleting
    the row inside the read -- exactly what a concurrent DELETE does.
    """
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we launch in APAC?").json()["runId"]
    client.post(f"/decisions/{run_id}/stop")

    real_get = decisions_repo.get_decision

    def get_then_delete(rid: str):
        item = real_get(rid)
        # delete_item directly, not delete_decision -- that calls get_decision,
        # which is the function being patched here.
        # The DELETE lands here. Straight SQL, not delete_decision() --
        # that calls the patched get_decision and would recurse.
        with connection() as conn:
            conn.execute("DELETE FROM decisions WHERE id = %s", (rid,))
        return item

    monkeypatch.setattr(decisions_repo, "get_decision", get_then_delete)
    decisions_repo.save_partial_decision(
        run_id,
        {"agent_reports": {"ceo": {"summary": "partial"}}, "overall_risk_assessment": []},
        [],
    )
    monkeypatch.setattr(decisions_repo, "get_decision", real_get)

    assert decisions_repo.get_decision(run_id) is None
    assert client.get(f"/decisions/{run_id}").status_code == 404
