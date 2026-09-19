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

from app import auth, db
from app.main import app
from scripts.create_tables import create_tables

DEFAULT_TEST_DSN = "postgresql://localhost:5432/openexec_test"

# Fixed so tests can assert against them directly rather than threading a
# generated id through. Every pre-auth test in this suite predates the
# concept of "a different user" -- they all exercise one caller's own data,
# which is what makes TEST_USER_ID the right default for the plain `client`
# fixture instead of something per-test.
TEST_USER_ID = "99999999-9999-9999-9999-999999999999"
OTHER_USER_ID = "88888888-8888-8888-8888-888888888888"


def _cookie_for(user_id: str) -> tuple[str, str]:
    """Builds a real, validly-signed session cookie the same way POST
    /auth/session does, via the public set_session_cookie helper -- so these
    tests exercise the same cookie format get_current_user actually verifies,
    not a hand-rolled stand-in that could drift from it."""
    from fastapi import Response

    response = Response()
    auth.set_session_cookie(response, user_id)
    raw = response.headers["set-cookie"].split(f"{auth.get_settings().session_cookie_name}=", 1)[1]
    raw = raw.split(";", 1)[0]
    return auth.get_settings().session_cookie_name, raw


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
def _reset_tables(database_url, monkeypatch):
    """Env + truncation, factored out of the client fixtures below so a test
    requesting more than one of them (e.g. `client` and `other_user_client`
    together, to prove cross-user isolation) truncates once, not once per
    fixture -- pytest caches a fixture by name per test, so this runs exactly
    once regardless of how many client fixtures depend on it, while each of
    those still gets its own independent TestClient/cookie jar."""
    monkeypatch.setenv("DATABASE_URL", database_url)
    # CASCADE because events references decisions; RESTART IDENTITY is a no-op
    # here (no sequences) but keeps the statement correct if one is ever added.
    with db.connection() as conn:
        conn.execute("TRUNCATE decisions, events RESTART IDENTITY CASCADE")


@pytest.fixture
def anon_client(_reset_tables):
    """No session cookie. The default `client` below carries one, since
    almost every existing test exercises one caller's own data and predates
    auth entirely -- use this one specifically to test the unauthenticated
    or cross-origin path."""
    yield TestClient(app)


#: Matches Settings.cors_origins' default (app/config.py), which is also what
#: OPENEXEC_CORS_ORIGINS resolves to when unset, as it is in this suite. A
#: real browser always sends a matching Origin on every mutating request; a
#: TestClient sends none unless told to, so every authenticated fixture below
#: sets one to stay a faithful stand-in for the real caller verify_origin
#: (app/auth.py) exists to allow. anon_client deliberately does not, so CSRF
#: tests can omit or mismatch it on purpose.
_ALLOWED_ORIGIN = "http://localhost:5173"


@pytest.fixture
def client(_reset_tables):
    c = TestClient(app, headers={"Origin": _ALLOWED_ORIGIN})
    name, value = _cookie_for(TEST_USER_ID)
    c.cookies.set(name, value)
    yield c


@pytest.fixture
def other_user_client(_reset_tables):
    """A second, distinct signed-in user sharing the same truncated table --
    for asserting that one user's decisions are invisible to another. A
    separate TestClient/cookie jar from `client`, not the same one recookied,
    so both can be used in the same test simultaneously."""
    c = TestClient(app, headers={"Origin": _ALLOWED_ORIGIN})
    name, value = _cookie_for(OTHER_USER_ID)
    c.cookies.set(name, value)
    yield c
