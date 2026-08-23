"""Create the two DynamoDB tables from Section 2 of the plan
(.claude/plans/curious-orbiting-shore.md). Idempotent — safe to re-run.

Usage (run from the backend/ directory so the `app` package resolves):
    python -m scripts.create_tables                 # against real AWS
    DYNAMODB_ENDPOINT_URL=http://localhost:8000 \\
        python -m scripts.create_tables              # against dynamodb-local

Every table/GSI is provisioned at 5 WCU/5 RCU. Four capacity groups total
(decisions table + its 2 GSIs + events table) = 20 WCU/20 RCU, comfortably
under the DynamoDB Always Free 25 WCU/25 RCU allowance with headroom.
"""

from __future__ import annotations

from app.config import get_settings
from app.db import get_dynamodb_resource

_THROUGHPUT = {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}


def create_decisions_table(dynamodb, table_name: str):
    return dynamodb.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "entity_type", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
            {"AttributeName": "parent_run_id", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        ProvisionedThroughput=_THROUGHPUT,
        GlobalSecondaryIndexes=[
            {
                "IndexName": "gsi_recency",
                "KeySchema": [
                    {"AttributeName": "entity_type", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": _THROUGHPUT,
            },
            {
                "IndexName": "gsi_parent",
                "KeySchema": [
                    {"AttributeName": "parent_run_id", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": _THROUGHPUT,
            },
        ],
    )


def create_events_table(dynamodb, table_name: str):
    return dynamodb.create_table(
        TableName=table_name,
        AttributeDefinitions=[
            {"AttributeName": "aggregate_id", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "aggregate_id", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        ProvisionedThroughput=_THROUGHPUT,
    )


def create_tables() -> None:
    settings = get_settings()
    dynamodb = get_dynamodb_resource()
    existing = {t.name for t in dynamodb.tables.all()}

    if settings.decisions_table not in existing:
        table = create_decisions_table(dynamodb, settings.decisions_table)
        table.wait_until_exists()
        print(f"Created table: {settings.decisions_table}")
    else:
        print(f"Table already exists, skipping: {settings.decisions_table}")

    if settings.events_table not in existing:
        table = create_events_table(dynamodb, settings.events_table)
        table.wait_until_exists()
        print(f"Created table: {settings.events_table}")
    else:
        print(f"Table already exists, skipping: {settings.events_table}")


if __name__ == "__main__":
    create_tables()
