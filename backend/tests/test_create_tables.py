"""Schema creation, against a real Postgres (see tests/conftest.py).

The session fixture has already applied the schema by the time these run, so
they double as a check that create_tables() is genuinely idempotent -- it has
now executed at least twice.
"""

from app.db import connection
from scripts.create_tables import create_tables


def _columns(table: str) -> dict[str, str]:
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name = %s
            """,
            (table,),
        ).fetchall()
    return {r["column_name"]: r["data_type"] for r in rows}


def test_creates_both_tables(client):
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        ).fetchall()
    assert {"decisions", "events"} <= {r["table_name"] for r in rows}


def test_rerunning_is_idempotent(client):
    # Every statement is CREATE ... IF NOT EXISTS, so this must not raise and
    # must not disturb existing rows.
    create_tables()
    create_tables()
    assert "id" in _columns("decisions")


def test_result_payload_is_jsonb_not_columns(client):
    """The hybrid shape is load-bearing: promoted columns for what is
    filtered or ordered on, one jsonb blob for everything else. If someone
    promotes a result field to a column, _row_to_item stops merging it."""
    columns = _columns("decisions")
    assert columns["data"] == "jsonb"
    assert columns["requested_agents"] == "jsonb"
    assert "agent_reports" not in columns
    assert "executive_summary" not in columns


def test_entity_type_is_gone(client):
    """It existed only as the gsi_recency partition key. ORDER BY needs no
    partition key, so carrying it into Postgres would be cargo cult."""
    assert "entity_type" not in _columns("decisions")


def test_recency_and_parent_indexes_exist(client):
    with connection() as conn:
        rows = conn.execute(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'decisions'"
        ).fetchall()
    names = {r["indexname"] for r in rows}
    assert "decisions_recency" in names
    assert "decisions_parent" in names


def test_events_cascade_on_decision_delete(client):
    """The DynamoDB version had no cascade, so a failure between the two
    delete calls in the router orphaned a whole timeline."""
    with connection() as conn:
        conn.execute(
            "INSERT INTO decisions (id, status, prompt) VALUES ('run-x', 'completed', 'p')"
        )
        conn.execute(
            "INSERT INTO events (aggregate_id, sk, type) VALUES ('run-x', '1#a', 't')"
        )
        conn.execute("DELETE FROM decisions WHERE id = 'run-x'")
        remaining = conn.execute(
            "SELECT count(*) AS n FROM events WHERE aggregate_id = 'run-x'"
        ).fetchone()
    assert remaining["n"] == 0
