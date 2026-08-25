"""Settings-file resolution for AIClient.

The default path is relative to the process working directory, which is a
deployment hazard: under systemd a wrong WorkingDirectory silently degrades
every agent to fallback output rather than failing.
"""

import json

import pytest

from openexec.ai.client import AIClient, resolve_settings_path


class TestResolveSettingsPath:
    def test_defaults_to_cwd_relative_settings_json(self, monkeypatch):
        monkeypatch.delenv("OPENEXEC_SETTINGS_PATH", raising=False)
        assert str(resolve_settings_path()) == "settings.json"

    def test_env_var_overrides_the_default(self, monkeypatch):
        monkeypatch.setenv("OPENEXEC_SETTINGS_PATH", "/etc/openexec/settings.json")
        assert str(resolve_settings_path()) == "/etc/openexec/settings.json"

    def test_explicit_argument_beats_the_env_var(self, monkeypatch):
        monkeypatch.setenv("OPENEXEC_SETTINGS_PATH", "/etc/openexec/settings.json")
        assert str(resolve_settings_path("/tmp/explicit.json")) == "/tmp/explicit.json"


class TestLoadSettings:
    def test_loads_from_the_env_var_path(self, monkeypatch, tmp_path):
        settings = tmp_path / "custom.json"
        settings.write_text(json.dumps({"ai": {"model": "from-env", "base_url": "http://x/v1"}}))
        monkeypatch.setenv("OPENEXEC_SETTINGS_PATH", str(settings))

        client = AIClient()

        assert client.provider.ai_config["model"] == "from-env"

    def test_missing_file_still_raises_with_the_resolved_path(self, monkeypatch, tmp_path):
        missing = tmp_path / "nope.json"
        monkeypatch.setenv("OPENEXEC_SETTINGS_PATH", str(missing))

        with pytest.raises(FileNotFoundError, match=str(missing)):
            AIClient()
