"""SSE stream — Section 3.4 of the plan. Replays stored events (always
testable today), then tails live events via the in-process event bus while a
decision's status is 'running' — that half stays dark until the deferred
orchestration phase actually calls event_bus.publish()."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.repositories import decisions as decisions_repo
from app.repositories import events as events_repo
from app.services import event_bus

router = APIRouter()

_TERMINAL_EVENT_TYPES = {"synthesis_completed", "error_occurred"}

# Longest silence allowed on a live tail before we put a byte on the wire
# anyway. Cloudflare closes a proxied connection that has been idle for 100s
# (HTTP 524) and that ceiling is fixed on every plan below Enterprise, so a
# quiet stretch -- one slow specialist LLM call between two events -- would
# otherwise kill the stream mid-deliberation. 30s leaves room to miss two
# beats and still stay under the limit. nginx alone never hit this because
# deploy/nginx.conf sets proxy_read_timeout 3600s; the proxy in front of it
# is the constraint.
_HEARTBEAT_SECONDS = 30


def to_wire_event(item: dict[str, Any]) -> dict[str, Any]:
    """Stored row (aggregate_id/sk/event_id/timestamp/type/payload) -> the
    flat shape frontend/src/api/types.ts's DeliberationEvent expects."""
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
        yield f"data: {json.dumps(to_wire_event(item))}\n\n"

    if not is_running:
        return

    queue = event_bus.subscribe(run_id)
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=_HEARTBEAT_SECONDS)
            except asyncio.TimeoutError:
                # An SSE comment frame. The spec has clients discard it, so no
                # handler ever sees it, but every proxy in the path counts it
                # as traffic and resets its idle timer.
                yield ": keepalive\n\n"
                continue
            yield f"data: {json.dumps(event)}\n\n"
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
