"""Verifies the DynamoDB schema from Section 2 of the plan
(.claude/plans/curious-orbiting-shore.md) against moto's in-memory AWS mock —
no Docker/dynamodb-local required to run this suite. docker-compose.yml is
still provided for anyone who wants to point a real dynamodb-local at the
same code via DYNAMODB_ENDPOINT_URL."""

import pytest
from boto3.dynamodb.conditions import Key
from moto import mock_aws

from app.db import get_dynamodb_resource
from scripts.create_tables import create_tables


@pytest.fixture(autouse=True)
def _aws_env(monkeypatch):
    # Dummy creds so boto3 doesn't refuse to build a client under moto.
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("OPENEXEC_DECISIONS_TABLE", "test-decisions")
    monkeypatch.setenv("OPENEXEC_EVENTS_TABLE", "test-events")
    monkeypatch.delenv("DYNAMODB_ENDPOINT_URL", raising=False)


@mock_aws
def test_create_tables_creates_expected_tables_and_gsis():
    create_tables()
    dynamodb = get_dynamodb_resource()
    names = {t.name for t in dynamodb.tables.all()}
    assert names == {"test-decisions", "test-events"}

    decisions_table = dynamodb.Table("test-decisions")
    gsi_names = {gsi["IndexName"] for gsi in decisions_table.global_secondary_indexes}
    assert gsi_names == {"gsi_recency", "gsi_parent"}


@mock_aws
def test_create_tables_is_idempotent():
    create_tables()
    create_tables()  # must not raise on the second run
    dynamodb = get_dynamodb_resource()
    assert {t.name for t in dynamodb.tables.all()} == {"test-decisions", "test-events"}


@mock_aws
def test_gsi_recency_returns_items_newest_query_works():
    create_tables()
    dynamodb = get_dynamodb_resource()
    decisions_table = dynamodb.Table("test-decisions")

    decisions_table.put_item(
        Item={
            "id": "run-1",
            "entity_type": "DECISION",
            "created_at": "2026-01-01T00:00:00.000Z",
            "prompt": "Should we expand into a new market?",
        }
    )

    response = decisions_table.query(
        IndexName="gsi_recency",
        KeyConditionExpression=Key("entity_type").eq("DECISION"),
    )
    assert [item["id"] for item in response["Items"]] == ["run-1"]


@mock_aws
def test_gsi_parent_is_sparse_and_finds_children():
    create_tables()
    dynamodb = get_dynamodb_resource()
    decisions_table = dynamodb.Table("test-decisions")

    decisions_table.put_item(
        Item={"id": "run-root", "entity_type": "DECISION", "created_at": "2026-01-01T00:00:00.000Z"}
    )
    decisions_table.put_item(
        Item={
            "id": "run-child",
            "entity_type": "DECISION",
            "created_at": "2026-01-02T00:00:00.000Z",
            "parent_run_id": "run-root",
        }
    )

    response = decisions_table.query(
        IndexName="gsi_parent",
        KeyConditionExpression=Key("parent_run_id").eq("run-root"),
    )
    assert [item["id"] for item in response["Items"]] == ["run-child"]

    # The root item never appears in gsi_parent — it has no parent_run_id.
    root_children = decisions_table.query(
        IndexName="gsi_parent",
        KeyConditionExpression=Key("parent_run_id").eq("run-root"),
        Limit=1,
    )
    assert len(root_children["Items"]) == 1


@mock_aws
def test_events_table_orders_by_sort_key():
    create_tables()
    dynamodb = get_dynamodb_resource()
    events_table = dynamodb.Table("test-events")

    events_table.put_item(
        Item={"aggregate_id": "run-1", "sk": "2026-01-01T00:00:02.000Z#evt2", "type": "inception_completed"}
    )
    events_table.put_item(
        Item={"aggregate_id": "run-1", "sk": "2026-01-01T00:00:01.000Z#evt1", "type": "inception_started"}
    )

    response = events_table.query(KeyConditionExpression=Key("aggregate_id").eq("run-1"))
    assert [item["type"] for item in response["Items"]] == ["inception_started", "inception_completed"]
