from tests.test_decisions import _submit


def test_stop_running_decision(client):
    run_id = _submit(client, "Should we launch in APAC?").json()["runId"]

    response = client.post(f"/decisions/{run_id}/stop")
    assert response.status_code == 200
    assert response.json() == {"status": "stopped"}


def test_stop_is_idempotent_once_stopped(client):
    run_id = _submit(client, "Should we launch in APAC?").json()["runId"]

    client.post(f"/decisions/{run_id}/stop")
    second = client.post(f"/decisions/{run_id}/stop")
    assert second.status_code == 200
    assert second.json() == {"status": "stopped"}


def test_stop_unknown_decision_returns_404(client):
    response = client.post("/decisions/does-not-exist/stop")
    assert response.status_code == 404
