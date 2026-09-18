"""Environment-driven settings. Same code runs locally, on a server, or
against a scratch Postgres in tests — only these values change, via env vars."""

import os
import secrets
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
    # Public half of the Supabase project's signing key. The project is on
    # asymmetric (ES256) keys, so this is everything needed to verify a token
    # and nothing that could mint one.
    supabase_jwks_url: str
    session_cookie_name: str
    # Signs the backend's own session cookie. See app/auth.py.
    session_secret: str


# Read once at import, not per call, so an unset OPENEXEC_SESSION_SECRET gives a
# secret that is stable for the process but different on every deployment and
# every restart. A hardcoded fallback would be the same on every install; the
# cost of this one is that restarting the API drops outstanding sessions, which
# is the right way for a missing secret to be noticed.
_EPHEMERAL_SESSION_SECRET = secrets.token_urlsafe(32)

DEFAULT_SUPABASE_JWKS_URL = (
    "https://kmnjzxbkvfcyycwcqwhz.supabase.co/auth/v1/.well-known/jwks.json"
)


def get_settings() -> Settings:
    cors_origins_raw = os.environ.get("OPENEXEC_CORS_ORIGINS", "http://localhost:5173")
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL", "postgresql://localhost:5432/openexec"
        ),
        cors_origins=[origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()],
        settings_file=os.environ.get("OPENEXEC_SETTINGS_PATH", "settings.json"),
        require_settings=os.environ.get("OPENEXEC_REQUIRE_SETTINGS", "").lower() in {"1", "true"},
        supabase_jwks_url=os.environ.get("SUPABASE_JWKS_URL", DEFAULT_SUPABASE_JWKS_URL),
        session_cookie_name=os.environ.get("OPENEXEC_SESSION_COOKIE", "oe_session"),
        session_secret=os.environ.get("OPENEXEC_SESSION_SECRET", _EPHEMERAL_SESSION_SECRET),
    )
