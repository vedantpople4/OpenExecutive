"""Postgres connection pool. Same code targets a local Postgres (tests, local
dev) or Supabase purely via DATABASE_URL -- see config.py.

Against Supabase, use the *session pooler* connection string, not the direct
one: direct connections are IPv6-only unless the project buys the IPv4 add-on,
and most hosts are IPv4. Transaction mode (port 6543) is built for serverless
and is the wrong mode for a long-lived server.

Nothing here coerces values on the way in. jsonb accepts floats and integer
keys, which is why the DynamoDB-era to_dynamodb_safe helper is gone rather
than ported.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import get_settings

_pool: ConnectionPool | None = None
_pool_url: str | None = None


def get_pool() -> ConnectionPool:
    """One pool per process, rebuilt if DATABASE_URL changes.

    The URL check is what lets the test suite point at a scratch database via
    monkeypatched env without a stale pool surviving from an earlier test.

    Small on purpose: uvicorn runs a single worker (see the orchestration
    notes), and Supabase's free tier is connection-constrained.
    """
    global _pool, _pool_url
    url = get_settings().database_url
    if _pool is None or _pool_url != url:
        close_pool()
        _pool = ConnectionPool(
            url,
            min_size=1,
            max_size=5,
            kwargs={"row_factory": dict_row},
            open=True,
        )
        _pool_url = url
    return _pool


def close_pool() -> None:
    global _pool, _pool_url
    if _pool is not None:
        _pool.close()
    _pool = None
    _pool_url = None


@contextmanager
def connection() -> Iterator[Any]:
    """A pooled connection in its own transaction, committed on clean exit."""
    with get_pool().connection() as conn:
        yield conn


def to_iso(value: Any) -> Any:
    """timestamptz -> the exact string shape the API has always returned.

    Postgres hands back datetimes; the wire format predates it and the
    frontend parses it, so the conversion happens here rather than leaking a
    changed contract. Mirrors the old _now_iso() precisely: milliseconds, and
    a literal Z rather than +00:00.
    """
    if not isinstance(value, datetime):
        return value
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
