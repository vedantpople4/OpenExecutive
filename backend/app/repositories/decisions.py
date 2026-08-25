"""DynamoDB access for openexec-decisions — Section 2.1 and 3.1-3.3 of the plan."""

from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from decimal import Decimal

from boto3.dynamodb.conditions import Key

from app.config import get_settings
from app.db import to_dynamodb_safe, get_dynamodb_resource


def _table():
    return get_dynamodb_resource().Table(get_settings().decisions_table)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _encode_cursor(key: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(key).encode()).decode()


def _decode_cursor(cursor: str) -> dict[str, Any]:
    return json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())


def create_decision(
    prompt: str,
    agents: list[str],
    team_mode_enabled: bool,
    parent_run_id: str | None,
) -> str:
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    now = _now_iso()
    item: dict[str, Any] = {
        "id": run_id,
        "entity_type": "DECISION",
        "status": "running",
        "created_at": now,
        "updated_at": now,
        "prompt": prompt,
        # Stored as a plain list, not the plan's DynamoDB String Set — SS
        # cannot be empty and nothing outside this repo reads the attribute.
        "requested_agents": agents,
        "team_mode_enabled": team_mode_enabled,
    }
    if parent_run_id is not None:
        item["parent_run_id"] = parent_run_id
    _table().put_item(Item=item)
    return run_id


def get_decision(run_id: str) -> dict[str, Any] | None:
    response = _table().get_item(Key={"id": run_id})
    return response.get("Item")


_TERMINAL_STATUSES = {"completed", "stopped", "error"}


def stop_decision(run_id: str) -> str | None:
    """Returns the resulting status, or None if the decision doesn't exist.
    No-op if already terminal — a finished run is never overwritten back to
    'stopped'."""
    item = get_decision(run_id)
    if item is None:
        return None
    if item.get("status") in _TERMINAL_STATUSES:
        return item["status"]

    _table().update_item(
        Key={"id": run_id},
        UpdateExpression="SET #status = :stopped, updated_at = :now",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":stopped": "stopped", ":now": _now_iso()},
    )
    return "stopped"


def _update_item(run_id: str, updates: dict[str, Any]) -> None:
    names = {f"#{k}": k for k in updates}
    values = {f":{k}": v for k, v in updates.items()}
    expr = "SET " + ", ".join(f"#{k} = :{k}" for k in updates)
    _table().update_item(
        Key={"id": run_id},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def _result_fields(
    final_results: dict[str, Any],
    action_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """The result payload shared by a completed and a cancelled run. Excludes
    status deliberately — the caller owns that."""
    agent_reports = final_results.get("agent_reports", {})
    overall_risk_assessment = final_results.get("overall_risk_assessment", [])
    return {
        "updated_at": _now_iso(),
        "agent_reports": to_dynamodb_safe(agent_reports),
        "deliberation_rounds": to_dynamodb_safe(final_results.get("deliberation_rounds", {})),
        "board_decision": to_dynamodb_safe(final_results.get("board_decision") or {}),
        "action_items": to_dynamodb_safe(action_items),
        "overall_risk_assessment": overall_risk_assessment,
        "synthesized_recommendations": final_results.get("synthesized_recommendations", []),
        "fallback_warnings": final_results.get("fallback_warnings", []),
        "executive_summary": final_results.get("executive_summary", ""),
        "decision_point": final_results.get("decision_point"),
        "top_risks": overall_risk_assessment[:3],
        "agent_alignment": {
            name: Decimal(str(report.get("alignment_score", 0.5)))
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

    _update_item(run_id, {"status": "completed", **_result_fields(final_results, action_items)})


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
        {"status": "error", "error_message": error_message, "updated_at": _now_iso()},
    )


def has_children(run_id: str) -> bool:
    response = _table().query(
        IndexName="gsi_parent",
        KeyConditionExpression=Key("parent_run_id").eq(run_id),
        Limit=1,
    )
    return len(response.get("Items", [])) > 0


def list_decisions(
    q: str | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[dict[str, Any]], str | None]:
    kwargs: dict[str, Any] = {
        "IndexName": "gsi_recency",
        "KeyConditionExpression": Key("entity_type").eq("DECISION"),
        "ScanIndexForward": False,
        "Limit": limit,
    }
    if cursor:
        kwargs["ExclusiveStartKey"] = _decode_cursor(cursor)

    response = _table().query(**kwargs)
    items = response.get("Items", [])

    if q:
        needle = q.lower()
        items = [item for item in items if needle in item.get("prompt", "").lower()]

    next_cursor = (
        _encode_cursor(response["LastEvaluatedKey"]) if "LastEvaluatedKey" in response else None
    )
    return items, next_cursor


def scan_all_decisions() -> list[dict[str, Any]]:
    """Full table Scan — used only by GET /dashboard (Section 3.7): a rare
    endpoint, small item count at this app's scale, well within the
    always-free 25 RCU allowance. Paginates internally since Scan caps each
    response at ~1MB."""
    table = _table()
    items: list[dict[str, Any]] = []
    kwargs: dict[str, Any] = {}
    while True:
        response = table.scan(**kwargs)
        items.extend(response.get("Items", []))
        if "LastEvaluatedKey" not in response:
            break
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
    return items


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
