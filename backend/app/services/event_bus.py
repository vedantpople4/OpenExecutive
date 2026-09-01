"""In-process pub/sub for live SSE tailing (Section 5 of the plan): the
future orchestration loop and the API server share one server process, so a
per-run asyncio.Queue is enough fan-out — no external broker needed at this
scale. Nothing publishes to this yet; the deferred LLM-orchestration phase
is the intended caller of publish()."""

from __future__ import annotations

import asyncio
from typing import Any

_subscribers: dict[str, list[asyncio.Queue]] = {}


def subscribe(run_id: str) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers.setdefault(run_id, []).append(queue)
    return queue


def unsubscribe(run_id: str, queue: asyncio.Queue) -> None:
    subscribers = _subscribers.get(run_id)
    if not subscribers:
        return
    if queue in subscribers:
        subscribers.remove(queue)
    if not subscribers:
        _subscribers.pop(run_id, None)


def publish(run_id: str, event: dict[str, Any]) -> None:
    for queue in _subscribers.get(run_id, []):
        queue.put_nowait(event)
