"""Postgres access for the events table.

Returns the same dict shape the DynamoDB version did -- aggregate_id, sk,
event_id, timestamp, type, payload -- so routers/events.py's to_wire_event is
untouched.
"""

from __future__ import annotations

import logging
from typing import Any

from psycopg.errors import ForeignKeyViolation
from psycopg.types.json import Json

from app.db import connection, to_iso

logger = logging.getLogger(__name__)

_COLUMNS = "aggregate_id, sk, event_id, timestamp, type, payload"


def _row_to_item(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    item["timestamp"] = to_iso(item.get("timestamp"))
    return item


def list_events(run_id: str) -> list[dict[str, Any]]:
    """All events for a run, in emission order.

    ORDER BY sk keeps the old guarantee: the sort key is ISO-timestamp
    prefixed, so lexicographic order is emission order. The paging loop the
    DynamoDB version needed is gone -- that existed only for the 1 MB
    response cap.
    """
    with connection() as conn:
        rows = conn.execute(
            f"SELECT {_COLUMNS} FROM events WHERE aggregate_id = %s ORDER BY sk",
            (run_id,),
        ).fetchall()
    return [_row_to_item(row) for row in rows]


def append_event(run_id: str, sk: str, event: dict[str, Any]) -> None:
    """Persist one event, unless its decision has been deleted underneath us.

    The foreign key makes an orphaned event impossible, which means a worker
    still emitting after its decision was deleted now hits a constraint rather
    than quietly writing a row nobody will ever read. Swallowing that mirrors
    what _update_item does with the same race in decisions.py: the run is
    gone, so dropping its trailing events is the whole point. Letting it
    raise would surface as a crashed worker thread instead.
    """
    try:
        _insert(run_id, sk, event)
    except ForeignKeyViolation:
        logger.info("Discarded event for deleted decision %s", run_id)


def _insert(run_id: str, sk: str, event: dict[str, Any]) -> None:
    # ON CONFLICT DO UPDATE rather than DO NOTHING: put_item overwrote, and a
    # replayed event should still land rather than silently vanish.
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO events (aggregate_id, sk, event_id, timestamp, type, payload)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (aggregate_id, sk) DO UPDATE SET
                event_id = EXCLUDED.event_id,
                timestamp = EXCLUDED.timestamp,
                type = EXCLUDED.type,
                payload = EXCLUDED.payload
            """,
            (
                run_id,
                sk,
                event.get("event_id"),
                event.get("timestamp"),
                event.get("type"),
                Json(event.get("payload") or {}),
            ),
        )


def delete_events(run_id: str) -> int:
    """Every event for a run. Returns how many were removed.

    The schema also cascades from decisions, so this is belt and braces -- but
    the router still calls it explicitly, and it is the only cleanup path for
    a table with no TTL.
    """
    with connection() as conn:
        cur = conn.execute("DELETE FROM events WHERE aggregate_id = %s", (run_id,))
        return cur.rowcount
