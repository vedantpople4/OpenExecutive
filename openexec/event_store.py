import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from openexec.events import Event


class EventStore:
    """Append-only event log for a simulation run's audit trail.

    Events are persisted to disk as JSON as they are emitted. The read/replay
    side (get_events/replay/load_from_disk/clear) was removed — nothing
    consumed it, so the trail is write-only by design.
    """

    def __init__(self, storage_path: str = "memory/events/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.events: list[Event] = []

    def append(self, event: Event) -> str:
        """Append an event to the store and persist to disk.

        Args:
            event: The event to append

        Returns:
            The event_id of the appended event
        """
        if not event.event_id:
            event.event_id = str(uuid.uuid4())

        self.events.append(event)
        self._persist_event(event)
        return event.event_id

    def _persist_event(self, event: Event) -> None:
        """Persist an event to disk as JSON."""
        timestamp_str = event.timestamp.isoformat()
        event_data = {
            "event_id": event.event_id,
            "timestamp": timestamp_str,
            "aggregate_id": event.aggregate_id,
            "event_type": event.event_type.value,
            **{k: v for k, v in self._extract_event_data(event).items() if v is not None}
        }

        filename = f"{event.event_id}.json"
        filepath = self.storage_path / filename
        with open(filepath, 'w') as f:
            json.dump(event_data, f, indent=2, default=str)

    def _extract_event_data(self, event: Event) -> Dict[str, Any]:
        """Extract relevant data from an event for serialization."""
        result = {}
        for key, value in event.__dict__.items():
            if key in ('event_id', 'timestamp', 'event_type', 'aggregate_id'):
                continue
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result