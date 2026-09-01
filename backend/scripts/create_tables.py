"""Apply schema.sql. Idempotent — safe to re-run.

Usage (run from the backend/ directory so the `app` package resolves):
    DATABASE_URL=postgresql://... python -m scripts.create_tables

Kept under its old name because the deploy runbook, CI and the test fixture
all invoke it; only what it does underneath has changed.
"""

from __future__ import annotations

from pathlib import Path

from app.db import connection

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def create_tables() -> None:
    # No parameters, so psycopg runs the whole file as one multi-statement
    # query -- and one transaction, so a half-applied schema is not possible.
    with connection() as conn:
        conn.execute(SCHEMA_PATH.read_text())
    print(f"Applied schema: {SCHEMA_PATH.name}")


if __name__ == "__main__":
    create_tables()
