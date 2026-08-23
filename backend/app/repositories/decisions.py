"""DynamoDB access for openexec-decisions — Section 2.1 and 3.1-3.3 of the plan."""

from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from boto3.dynamodb.conditions import Key

from app.config import get_settings
from app.db import get_dynamodb_resource


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
    }
