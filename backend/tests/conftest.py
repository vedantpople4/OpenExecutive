"""Test fixtures.

The suite runs against a real Postgres. There is no in-memory stand-in the way
moto stood in for DynamoDB, and SQLite is not faithful enough -- the
repositories lean on jsonb and ILIKE.

    local:  brew services start postgresql@16 && createdb openexec_test
    CI:     the postgres:16 service in .github/workflows/ci.yml

Override the target with DATABASE_URL.
"""

import os

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app
from scripts.create_tables import create_tables

DEFAULT_TEST_DSN = "postgresql://localhost:5432/openexec_test"


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_TEST_DSN)


@pytest.fixture(scope="session", autouse=True)
def _schema(database_url):
    """Create the schema once for the whole session; per-test isolation is
    truncation, which is far cheaper than rebuilding it each time."""
    os.environ["DATABASE_URL"] = database_url
    create_tables()
    yield
    db.close_pool()


@pytest.fixture
def client(database_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", database_url)
    # CASCADE because events references decisions; RESTART IDENTITY is a no-op
    # here (no sequences) but keeps the statement correct if one is ever added.
    with db.connection() as conn:
        conn.execute("TRUNCATE decisions, events RESTART IDENTITY CASCADE")
    yield TestClient(app)
