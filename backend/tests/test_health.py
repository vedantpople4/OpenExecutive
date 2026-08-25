from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    # Present even without a lifespan run (this client never enters one), so
    # the shape is stable for callers.
    assert "settings_path" in body
    assert "settings_found" in body
