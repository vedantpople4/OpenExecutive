"""Postgres access for the decisions table.

Every function keeps the signature and the dict shape it had under DynamoDB:
callers get a flat dict whose keys are the promoted columns merged with the
contents of the jsonb `data` blob. That is what lets routers, services,
to_summary and to_detail carry over untouched.
"""

from __future__ import annotations

import base64
import json
import logging
import uuid
from typing import Any

from psycopg.types.json import Json

from app.db import connection, to_iso

logger = logging.getLogger(__name__)

# Promoted to real columns because something filters, orders or joins on them.
# Anything else in an update goes into the jsonb blob.
_COLUMN_FIELDS = {
    "status",
    "prompt",
    "parent_run_id",
    "team_mode_enabled",
    "requested_agents",
}

_SELECT = """
    id, status, created_at, updated_at, prompt, parent_run_id,
    team_mode_enabled, requested_agents, data
"""


def _row_to_item(row: dict[str, Any]) -> dict[str, Any]:
    """Column values merged with the jsonb blob, flat, as callers expect."""
    item = dict(row)
    data = item.pop("data", None) or {}
    item["created_at"] = to_iso(item.get("created_at"))
    item["updated_at"] = to_iso(item.get("updated_at"))
    item.update(data)
    return item


def _encode_cursor(created_at: str, run_id: str) -> str:
    return base64.urlsafe_b64encode(json.dumps([created_at, run_id]).encode()).decode()


def _decode_cursor(cursor: str) -> tuple[str, str]:
    created_at, run_id = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    return created_at, run_id


def create_decision(
    prompt: str,
    agents: list[str],
    team_mode_enabled: bool,
    parent_run_id: str | None,
) -> str:
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO decisions
                (id, status, prompt, parent_run_id, team_mode_enabled, requested_agents)
            VALUES (%s, 'running', %s, %s, %s, %s)
            """,
            (run_id, prompt, parent_run_id, team_mode_enabled, Json(agents)),
        )
    return run_id


def get_decision(run_id: str) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute(
            f"SELECT {_SELECT} FROM decisions WHERE id = %s", (run_id,)
        ).fetchone()
    return _row_to_item(row) if row else None


_TERMINAL_STATUSES = {"completed", "stopped", "error"}


def stop_decision(run_id: str) -> str | None:
    """Returns the resulting status, or None if the decision doesn't exist.
    No-op if already terminal — a finished run is never overwritten back to
    'stopped'.

    One statement rather than read-then-write: the status guard is in the
    WHERE clause, so a run that finishes mid-call cannot be reverted.
    """
    with connection() as conn:
        row = conn.execute(
            """
            UPDATE decisions SET status = 'stopped', updated_at = now()
            WHERE id = %s AND status NOT IN ('completed', 'stopped', 'error')
            RETURNING status
            """,
            (run_id,),
        ).fetchone()
        if row is not None:
            return row["status"]

        existing = conn.execute(
            "SELECT status FROM decisions WHERE id = %s", (run_id,)
        ).fetchone()
    return existing["status"] if existing else None


def delete_decision(run_id: str) -> bool:
    """Removes the decision row. False if it was not there to begin with.

    Events go too, via ON DELETE CASCADE -- but routers/decisions.py still
    deletes them explicitly first, so the behaviour does not depend on the
    constraint being present.
    """
    with connection() as conn:
        cur = conn.execute("DELETE FROM decisions WHERE id = %s", (run_id,))
        return cur.rowcount > 0


def _update_item(run_id: str, updates: dict[str, Any]) -> None:
    """Writes result fields back, but only onto a decision that still exists.

    Under DynamoDB this needed an explicit ConditionExpression, because
    update_item is an upsert and a worker finishing after its decision was
    deleted would silently recreate the row. UPDATE simply matches no rows,
    so the guard is now `rowcount == 0` -- same protection, no condition
    expression.

    That is a real sequence: stop a run, delete it from the history, and the
    worker's in-flight LLM call returns up to two minutes later and tries to
    write partial results to a key nobody expects to exist any more.
    """
    columns = {k: v for k, v in updates.items() if k in _COLUMN_FIELDS}
    blob = {k: v for k, v in updates.items() if k not in _COLUMN_FIELDS}

    # Every write bumps updated_at, so callers never pass it -- and it is set
    # in SQL rather than bound, since now() is a function call not a value.
    assignments = ["updated_at = now()"] + [f"{key} = %({key})s" for key in columns]
    params: dict[str, Any] = dict(columns)
    if "requested_agents" in params:
        params["requested_agents"] = Json(params["requested_agents"])
    if blob:
        # || merges into the existing blob rather than replacing it, matching
        # the per-attribute SET the DynamoDB version did.
        assignments.append("data = data || %(_blob)s::jsonb")
        params["_blob"] = Json(blob)
    params["_id"] = run_id

    with connection() as conn:
        cur = conn.execute(
            f"UPDATE decisions SET {', '.join(assignments)} WHERE id = %(_id)s", params
        )
        if cur.rowcount == 0:
            # Deleted mid-flight. Dropping the write is the whole point.
            logger.info("Discarded results for deleted decision %s", run_id)


def _result_fields(
    final_results: dict[str, Any],
    action_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """The result payload shared by a completed and a cancelled run. Excludes
    status deliberately — the caller owns that.

    No float/Decimal coercion and no stringified map keys: jsonb takes both,
    which is why to_dynamodb_safe did not survive the move.
    """
    agent_reports = final_results.get("agent_reports", {})
    overall_risk_assessment = final_results.get("overall_risk_assessment", [])
    return {
        "agent_reports": agent_reports,
        "deliberation_rounds": final_results.get("deliberation_rounds", {}),
        "board_decision": final_results.get("board_decision") or {},
        "action_items": action_items,
        "overall_risk_assessment": overall_risk_assessment,
        "synthesized_recommendations": final_results.get("synthesized_recommendations", []),
        "fallback_warnings": final_results.get("fallback_warnings", []),
        "executive_summary": final_results.get("executive_summary", ""),
        "decision_point": final_results.get("decision_point"),
        "top_risks": overall_risk_assessment[:3],
        "agent_alignment": {
            name: float(report.get("alignment_score", 0.5))
            for name, report in agent_reports.items()
        },
        "action_item_count": len(action_items),
    }


def complete_decision(
    run_id: str,
    final_results: dict[str, Any],
    action_items: list[dict[str, Any]],
) -> None:
    """Populate the result fields from a finished orchestration run and mark
    the decision completed. No-op if the decision is already terminal (e.g.
    a stop request beat the background run to it) — a finished/stopped run
    is never overwritten back to 'completed'."""
    item = get_decision(run_id)
    if item is None or item.get("status") in _TERMINAL_STATUSES:
        return

    _update_item(
        run_id,
        {"status": "completed", **_result_fields(final_results, action_items)},
    )


def save_partial_decision(
    run_id: str,
    final_results: dict[str, Any],
    action_items: list[dict[str, Any]],
) -> None:
    """Write whatever a cancelled run produced WITHOUT touching status — the run
    is already 'stopped', or about to be, and that label must survive.

    The guard admits 'stopped' (that is the whole point) and 'running' (the
    worker can finish before the stop request's status write lands). It rejects
    only genuinely finished runs, so a late partial write can never clobber a
    real result."""
    item = get_decision(run_id)
    if item is None or item.get("status") in {"completed", "error"}:
        return

    _update_item(run_id, _result_fields(final_results, action_items))


def fail_decision(run_id: str, error_message: str) -> None:
    """No-op if the decision is already terminal — same reasoning as
    complete_decision above."""
    item = get_decision(run_id)
    if item is None or item.get("status") in _TERMINAL_STATUSES:
        return

    _update_item(
        run_id,
        {"status": "error", "error_message": error_message},
    )


def has_children(run_id: str) -> bool:
    with connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM decisions WHERE parent_run_id = %s LIMIT 1", (run_id,)
        ).fetchone()
    return row is not None


def list_decisions(
    q: str | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[dict[str, Any]], str | None]:
    """Newest first, keyset paginated.

    The q filter is applied in SQL, before the limit. The DynamoDB version
    fetched a page and filtered it in Python afterwards, so a search only ever
    matched within the current page and returned short pages -- that is fixed
    here, and it is a visible behaviour change.

    Keyset rather than OFFSET so a decision created mid-scroll cannot shift
    every later page by one. (created_at, id) is a total order thanks to the
    id tiebreaker in decisions_recency.
    """
    where = []
    params: dict[str, Any] = {"limit": limit}

    if q:
        where.append("prompt ILIKE %(pattern)s")
        params["pattern"] = f"%{q}%"
    if cursor:
        created_at, run_id = _decode_cursor(cursor)
        where.append("(created_at, id) < (%(after_ts)s, %(after_id)s)")
        params["after_ts"] = created_at
        params["after_id"] = run_id

    clause = f"WHERE {' AND '.join(where)}" if where else ""
    with connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_SELECT} FROM decisions
            {clause}
            ORDER BY created_at DESC, id DESC
            LIMIT %(limit)s
            """,
            params,
        ).fetchall()

    items = [_row_to_item(row) for row in rows]
    # Only a full page can have more behind it.
    next_cursor = (
        _encode_cursor(items[-1]["created_at"], items[-1]["id"])
        if len(items) == limit
        else None
    )
    return items, next_cursor


def scan_all_decisions() -> list[dict[str, Any]]:
    """Every decision — used only by GET /dashboard, a rare endpoint with a
    small row count at this app's scale. The internal paging loop the
    DynamoDB version carried is gone; it existed only for Scan's 1 MB cap."""
    with connection() as conn:
        rows = conn.execute(f"SELECT {_SELECT} FROM decisions").fetchall()
    return [_row_to_item(row) for row in rows]


def to_summary(item: dict[str, Any], has_children_flag: bool) -> dict[str, Any]:
    return {
        "runId": item["id"],
        "timestamp": item.get("created_at", ""),
        "prompt": item.get("prompt", ""),
        "decisionPoint": item.get("decision_point"),
        "executiveSummary": item.get("executive_summary"),
        "actionItemCount": int(item.get("action_item_count", 0)),
        "topRisks": list(item.get("top_risks", [])),
        "agentAlignment": {k: float(v) for k, v in item.get("agent_alignment", {}).items()},
        "parentRunId": item.get("parent_run_id"),
        "hasChildren": has_children_flag,
        "status": item.get("status"),
    }


def to_detail(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "runId": item["id"],
        "timestamp": item.get("created_at", ""),
        "prompt": item.get("prompt", ""),
        "decision_point": item.get("decision_point"),
        "executive_summary": item.get("executive_summary", ""),
        "parentRunId": item.get("parent_run_id"),
        "agent_reports": item.get("agent_reports", {}),
        "deliberation_rounds": item.get("deliberation_rounds", {}),
        "board_decision": item.get("board_decision", {}),
        "action_items": item.get("action_items", []),
        "overall_risk_assessment": item.get("overall_risk_assessment", []),
        "synthesized_recommendations": item.get("synthesized_recommendations", []),
        "fallback_warnings": item.get("fallback_warnings", []),
        # Without these two the API cannot express that a run failed or was
        # stopped -- the frontend would render a failed run as a normal,
        # complete-looking transcript.
        "status": item.get("status"),
        "error_message": item.get("error_message"),
    }
