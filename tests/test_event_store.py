"""Tests for openexec.event_store — append-only write trail persistence."""

import json
from datetime import datetime

from openexec.event_store import EventStore
from openexec.events import AgentReportGenerated, EventType


def _event():
    return AgentReportGenerated(
        event_id="evt-1",
        aggregate_id="sim-1",
        agent_name="ceo",
        report_data={"title": "x"},
    )


class TestEventStore:
    def test_append_returns_event_id(self, tmp_path):
        store = EventStore(storage_path=str(tmp_path))
        event = _event()
        assert store.append(event) == "evt-1"

    def test_append_assigns_id_when_missing(self, tmp_path):
        store = EventStore(storage_path=str(tmp_path))
        event = AgentReportGenerated(event_id="", agent_name="cfo")
        event_id = store.append(event)
        assert event_id  # a generated uuid

    def test_append_persists_json_to_disk(self, tmp_path):
        store = EventStore(storage_path=str(tmp_path))
        store.append(_event())
        persisted = tmp_path / "evt-1.json"
        assert persisted.exists()
        data = json.loads(persisted.read_text())
        assert data["event_id"] == "evt-1"
        assert data["aggregate_id"] == "sim-1"
        assert data["event_type"] == "agent_report_generated"
        assert data["agent_name"] == "ceo"
        assert data["timestamp"]

    def test_event_kept_in_memory(self, tmp_path):
        store = EventStore(storage_path=str(tmp_path))
        event = _event()
        store.append(event)
        assert store.events == [event]

    def test_none_values_stripped_from_payload(self, tmp_path):
        store = EventStore(storage_path=str(tmp_path))
        store.append(_event())
        data = json.loads((tmp_path / "evt-1.json").read_text())
        assert "report_data" in data  # non-null field preserved

    def test_creates_storage_dir(self, tmp_path):
        nested = tmp_path / "a" / "b"
        EventStore(storage_path=str(nested))
        assert nested.exists()

    def test_isoformat_timestamp_serializable(self, tmp_path):
        store = EventStore(storage_path=str(tmp_path))
        event = _event()
        event.timestamp = datetime(2026, 8, 1, 12, 0, 0)
        store.append(event)
        data = json.loads((tmp_path / "evt-1.json").read_text())
        assert data["timestamp"] == "2026-08-01T12:00:00"

    def test_event_type_value_serialized(self, tmp_path):
        store = EventStore(storage_path=str(tmp_path))
        store.append(_event())
        data = json.loads((tmp_path / "evt-1.json").read_text())
        assert data["event_type"] == EventType.AGENT_REPORT_GENERATED.value
