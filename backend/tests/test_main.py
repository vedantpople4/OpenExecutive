import pytest
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


def test_probe_reports_settings_when_present(monkeypatch, tmp_path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}")
    monkeypatch.setenv("OPENEXEC_SETTINGS_PATH", str(settings_file))
    monkeypatch.setenv("OPENEXEC_REQUIRE_SETTINGS", "1")

    try:
        with TestClient(app) as client:
            body = client.get("/health").json()
            assert body["settings_found"] is True
            assert body["settings_path"] == str(settings_file)
    finally:
        orchestration.set_main_loop(None)


def test_probe_fails_startup_when_required_and_missing(monkeypatch, tmp_path):
    """What makes a bad systemd WorkingDirectory a crash-loop instead of a
    silent run of stub reports."""
    monkeypatch.setenv("OPENEXEC_SETTINGS_PATH", str(tmp_path / "nope.json"))
    monkeypatch.setenv("OPENEXEC_REQUIRE_SETTINGS", "1")

    try:
        with pytest.raises(RuntimeError, match="LLM settings not found"):
            with TestClient(app):
                pass
    finally:
        orchestration.set_main_loop(None)


def test_probe_only_warns_when_not_required(monkeypatch, tmp_path):
    """The default. Keeps CI green, where no settings.json exists, and keeps
    history and dashboard endpoints serving when the LLM is misconfigured."""
    monkeypatch.setenv("OPENEXEC_SETTINGS_PATH", str(tmp_path / "nope.json"))
    monkeypatch.delenv("OPENEXEC_REQUIRE_SETTINGS", raising=False)

    try:
        with TestClient(app) as client:
            body = client.get("/health").json()
            assert body["status"] == "ok"
            assert body["settings_found"] is False
    finally:
        orchestration.set_main_loop(None)
