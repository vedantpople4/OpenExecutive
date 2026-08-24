"""Adapter satisfying openexec.orchestrator.Orchestrator's duck-typed
event-store contract (any object with .append(event) -> str, see
Orchestrator.set_event_store) -- fans each event out to DynamoDB persistence
and the live SSE pub/sub, instead of openexec's own disk-writing EventStore.

The two destinations need two different shapes for the same event:
- Persisted (backend/app/repositories/events.py): nested {..., payload: {...}}
  -- app/routers/events.py's to_wire_event() flattens payload on replay.
- Live-tailed (app/services/event_bus.py): must already be flat -- the SSE
  live-tail branch yields the dict as-is, with no to_wire_event() transform.
"""

from __future__ import annotations

import asyncio
import dataclasses
from datetime import datetime
from typing import Any

from app.db import to_dynamodb_safe
from app.repositories import events as events_repo
from app.services import event_bus


class BackendEventSink:
    def __init__(self, run_id: str, loop: asyncio.AbstractEventLoop | None) -> None:
        self._run_id = run_id
        self._loop = loop

    def append(self, event: Any) -> str:
        data = dataclasses.asdict(event)
        event_id: str = data.pop("event_id")
        timestamp = data.pop("timestamp")
        data.pop("aggregate_id", None)
        event_type = data.pop("event_type")

        timestamp_str = timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)
        type_str = event_type.value if hasattr(event_type, "value") else str(event_type)

        events_repo.append_event(
            self._run_id,
            sk=f"{timestamp_str}#{event_id}",
            event={
                "event_id": event_id,
                "timestamp": timestamp_str,
                "type": type_str,
                "payload": to_dynamodb_safe(data),
            },
        )

        if self._loop is not None:
            live_event = {
                "event_id": event_id,
                "timestamp": timestamp_str,
                "aggregate_id": self._run_id,
                "type": type_str,
                **data,
            }
            self._loop.call_soon_threadsafe(event_bus.publish, self._run_id, live_event)

        return event_id
