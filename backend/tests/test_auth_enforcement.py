"""Proves the two properties the auth work exists for: one user's data is
invisible to another, and a cross-origin request cannot act as a signed-in
user even with a valid cookie attached."""

from fastapi.testclient import TestClient

from app.main import app
from app.services import orchestration
from tests.conftest import TEST_USER_ID, _cookie_for
from tests.test_decisions import _submit


def test_list_decisions_requires_a_session(anon_client):
    response = anon_client.get("/decisions")
    assert response.status_code == 401


def test_dashboard_requires_a_session(anon_client):
    response = anon_client.get("/dashboard")
    assert response.status_code == 401


def test_stream_events_requires_a_session(anon_client):
    response = anon_client.get("/decisions/run-anything/events")
    assert response.status_code == 401


def test_a_users_decision_is_invisible_to_another_user(client, other_user_client, monkeypatch):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we open an office in Berlin?").json()["runId"]

    own_read = client.get(f"/decisions/{run_id}")
    assert own_read.status_code == 200

    other_read = other_user_client.get(f"/decisions/{run_id}")
    assert other_read.status_code == 404


def test_list_decisions_only_returns_the_callers_own(client, other_user_client, monkeypatch):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    _submit(client, "Mine")
    _submit(other_user_client, "Not mine")

    body = client.get("/decisions").json()
    prompts = [item["prompt"] for item in body["items"]]
    assert prompts == ["Mine"]


def test_dashboard_only_aggregates_the_callers_own(client, other_user_client, monkeypatch):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    _submit(client, "Mine")
    _submit(other_user_client, "Not mine")

    assert client.get("/dashboard").json()["total_decisions"] == 1


def test_cannot_delete_another_users_decision(client, other_user_client, monkeypatch):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we open an office in Berlin?").json()["runId"]

    response = other_user_client.delete(f"/decisions/{run_id}")
    assert response.status_code == 404
    # And it's still there, for its actual owner.
    assert client.get(f"/decisions/{run_id}").status_code == 200


def test_cannot_stop_another_users_decision(client, other_user_client, monkeypatch):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we open an office in Berlin?").json()["runId"]

    response = other_user_client.post(f"/decisions/{run_id}/stop")
    assert response.status_code == 404


def test_cannot_compare_a_decision_that_belongs_to_someone_else(
    client, other_user_client, monkeypatch
):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    mine = _submit(client, "Mine").json()["runId"]
    theirs = _submit(other_user_client, "Theirs").json()["runId"]

    response = client.get("/compare", params={"old": mine, "new": theirs})
    assert response.status_code == 404


def test_submit_decision_without_a_matching_origin_is_rejected(anon_client):
    """A cookie alone is not enough. This is the CSRF-shaped attack the human
    asked to be closed: a link or an auto-submitting form on another site
    cannot act as a signed-in user even if the browser attaches the cookie,
    because that request either carries no Origin header (most such vectors)
    or one that does not match this app's own."""
    name, value = _cookie_for(TEST_USER_ID)
    client_no_origin = TestClient(app)
    client_no_origin.cookies.set(name, value)
    response = client_no_origin.post(
        "/decisions",
        json={"prompt": "x", "agents": ["ceo"], "teamModeEnabled": False},
    )
    assert response.status_code == 403

    client_wrong_origin = TestClient(app, headers={"Origin": "https://evil.example"})
    client_wrong_origin.cookies.set(name, value)
    response = client_wrong_origin.post(
        "/decisions",
        json={"prompt": "x", "agents": ["ceo"], "teamModeEnabled": False},
    )
    assert response.status_code == 403


def test_stop_and_delete_also_require_a_matching_origin(client, monkeypatch):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we open an office in Berlin?").json()["runId"]

    name, value = _cookie_for(TEST_USER_ID)
    forged = TestClient(app, headers={"Origin": "https://evil.example"})
    forged.cookies.set(name, value)

    assert forged.post(f"/decisions/{run_id}/stop").status_code == 403
    assert forged.delete(f"/decisions/{run_id}").status_code == 403
    # Confirms the 403s above were real refusals, not accidental 404s: the
    # legitimate owner, same-origin (client already carries the right Origin
    # by default), can still act on it.
    assert client.post(f"/decisions/{run_id}/stop").status_code == 200
