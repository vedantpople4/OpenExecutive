"""Environment-driven settings. Same code runs locally, on EC2, or against
dynamodb-local — only these values change, via env vars."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    aws_region: str
    dynamodb_endpoint_url: str | None  # set for dynamodb-local; None on real AWS
    decisions_table: str
    events_table: str
    cors_origins: list[str]
    # Where openexec looks for its LLM config, and whether a missing file is
    # fatal at boot. See the probe in app/main.py.
    settings_file: str
    require_settings: bool


def get_settings() -> Settings:
    cors_origins_raw = os.environ.get("OPENEXEC_CORS_ORIGINS", "http://localhost:5173")
    return Settings(
        aws_region=os.environ.get("AWS_REGION", "us-east-1"),
        dynamodb_endpoint_url=os.environ.get("DYNAMODB_ENDPOINT_URL") or None,
        decisions_table=os.environ.get("OPENEXEC_DECISIONS_TABLE", "openexec-decisions"),
        events_table=os.environ.get("OPENEXEC_EVENTS_TABLE", "openexec-events"),
        cors_origins=[origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()],
        settings_file=os.environ.get("OPENEXEC_SETTINGS_PATH", "settings.json"),
        require_settings=os.environ.get("OPENEXEC_REQUIRE_SETTINGS", "").lower() in {"1", "true"},
    )
