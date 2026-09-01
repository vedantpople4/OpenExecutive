"""Environment-driven settings. Same code runs locally, on a server, or
against a scratch Postgres in tests — only these values change, via env vars."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Supabase: use the session-pooler string. See the note in app/db.py.
    database_url: str
    cors_origins: list[str]
    # Where openexec looks for its LLM config, and whether a missing file is
    # fatal at boot. See the probe in app/main.py.
    settings_file: str
    require_settings: bool


def get_settings() -> Settings:
    cors_origins_raw = os.environ.get("OPENEXEC_CORS_ORIGINS", "http://localhost:5173")
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL", "postgresql://localhost:5432/openexec"
        ),
        cors_origins=[origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()],
        settings_file=os.environ.get("OPENEXEC_SETTINGS_PATH", "settings.json"),
        require_settings=os.environ.get("OPENEXEC_REQUIRE_SETTINGS", "").lower() in {"1", "true"},
    )
