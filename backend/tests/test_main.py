from fastapi.testclient import TestClient

from app.main import app
from app.services import orchestration


def test_lifespan_captures_the_running_event_loop():
    try:
        with TestClient(app) as client:
            assert orchestration.get_main_loop() is not None
            assert client.get("/health").status_code == 200
    finally:
        # The loop above is closed once this `with` block exits -- clear the
        # reference so later tests (which call run_deliberation without ever
        # going through a real lifespan) see loop=None, not a closed loop.
        orchestration.set_main_loop(None)
