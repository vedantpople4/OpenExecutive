"""SSE stream — Section 3.4 of the plan. Replays stored events (always
testable today), then tails live events via the in-process event bus while a
decision's status is 'running' — that half stays dark until the deferred
orchestration phase actually calls event_bus.publish()."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.repositories import decisions as decisions_repo
from app.repositories import events as events_repo
from app.services import event_bus

router = APIRouter()

_TERMINAL_EVENT_TYPES = {"synthesis_completed", "error_occurred"}


def _json_default(value: Any) -> Any:
    # Raw DynamoDB items surface Decimal for every numeric attribute (see the
    # note in app/db.py) — json.dumps doesn't know how to serialize it.
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def to_wire_event(item: dict[str, Any]) -> dict[str, Any]:
    """DynamoDB item (aggregate_id/sk/event_id/timestamp/type/payload) ->
    the flat shape frontend/src/api/types.ts's DeliberationEvent expects."""
    payload = item.get("payload") or {}
    return {
        "event_id": item.get("event_id", ""),
        "timestamp": item.get("timestamp", ""),
        "aggregate_id": item.get("aggregate_id", ""),
        "type": item.get("type", ""),
        **payload,
    }


async def event_stream(run_id: str, is_running: bool) -> AsyncIterator[str]:
    for item in events_repo.list_events(run_id):
        yield f"data: {json.dumps(to_wire_event(item), default=_json_default)}\n\n"

    if not is_running:
        return

    queue = event_bus.subscribe(run_id)
    try:
        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event, default=_json_default)}\n\n"
            if event.get("type") in _TERMINAL_EVENT_TYPES:
                break
    finally:
        event_bus.unsubscribe(run_id, queue)


@router.get("/decisions/{run_id}/events")
def stream_events(run_id: str) -> StreamingResponse:
    decision = decisions_repo.get_decision(run_id)
    if decision is None:
        raise HTTPException(status_code=404, detail=f"Decision not found: {run_id}")

    is_running = decision.get("status") == "running"
    return StreamingResponse(event_stream(run_id, is_running), media_type="text/event-stream")
