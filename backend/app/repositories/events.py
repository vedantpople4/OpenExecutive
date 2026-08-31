"""DynamoDB access for openexec-events — Section 2.2 and 3.4 of the plan."""

from __future__ import annotations

from typing import Any

from boto3.dynamodb.conditions import Key

from app.config import get_settings
from app.db import get_dynamodb_resource


def _table():
    return get_dynamodb_resource().Table(get_settings().events_table)


def list_events(run_id: str) -> list[dict[str, Any]]:
    """All events for a run, in emission order — the sort key (ISO
    timestamp prefix) already guarantees ascending order for free."""
    items: list[dict[str, Any]] = []
    kwargs: dict[str, Any] = {"KeyConditionExpression": Key("aggregate_id").eq(run_id)}
    while True:
        response = _table().query(**kwargs)
        items.extend(response.get("Items", []))
        if "LastEvaluatedKey" not in response:
            break
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
    return items


def append_event(run_id: str, sk: str, event: dict[str, Any]) -> None:
    _table().put_item(Item={"aggregate_id": run_id, "sk": sk, **event})


def delete_events(run_id: str) -> int:
    """Every event for a run. Returns how many were removed.

    The events table has no TTL and no cascade, so deleting a decision without
    this leaves its whole timeline behind -- invisible in the UI but still
    billed, and still replayed if the same run id were ever reused.
    """
    items = list_events(run_id)
    if not items:
        return 0
    table = _table()
    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={"aggregate_id": item["aggregate_id"], "sk": item["sk"]})
    return len(items)
