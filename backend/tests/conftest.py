import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.main import app
from scripts.create_tables import create_tables


@pytest.fixture
def dynamo_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("OPENEXEC_DECISIONS_TABLE", "test-decisions")
    monkeypatch.setenv("OPENEXEC_EVENTS_TABLE", "test-events")
    monkeypatch.delenv("DYNAMODB_ENDPOINT_URL", raising=False)


@pytest.fixture
def client(dynamo_env):
    with mock_aws():
        create_tables()
        yield TestClient(app)
