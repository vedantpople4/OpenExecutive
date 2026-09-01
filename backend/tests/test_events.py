import asyncio
import json
from decimal import Decimal

from app.repositories import events as events_repo
from app.routers import events as events_router
from app.routers.events import event_stream
from app.services import event_bus, orchestration
from tests.test_decisions import _submit


def _sse_data_lines(body: str) -> list[dict]:
    return [
        json.loads(line[len("data: ") :])
        for line in body.splitlines()
        if line.startswith("data: ")
    ]


def test_events_stream_404_for_unknown_decision(client):
    response = client.get("/decisions/does-not-exist/events")
    assert response.status_code == 404


def test_events_stream_replays_stored_events_for_finished_decision(client, monkeypatch):
    # Without this, the real orchestrator would run to completion during
    # _submit() (TestClient runs BackgroundTasks synchronously) and its own
    # emitted events would pollute this test's hand-appended fixture events.
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we launch in APAC?").json()["runId"]
    client.post(f"/decisions/{run_id}/stop")  # -> terminal status, no live tail

    events_repo.append_event(
        run_id,
        "2026-01-01T00:00:01.000Z#e1",
        {
            "event_id": "e1",
            "timestamp": "2026-01-01T00:00:01.000Z",
            "type": "inception_started",
            "payload": {},
        },
    )
    events_repo.append_event(
        run_id,
        "2026-01-01T00:00:02.000Z#e2",
        {
            "event_id": "e2",
            "timestamp": "2026-01-01T00:00:02.000Z",
            "type": "agent_report_generated",
            "payload": {"agent_name": "ceo", "report_data": {"alignment_score": Decimal("0.8")}},
        },
    )

    response = client.get(f"/decisions/{run_id}/events")
    assert response.status_code == 200
    events = _sse_data_lines(response.text)

    assert [e["type"] for e in events] == ["inception_started", "agent_report_generated"]
    assert events[1]["agent_name"] == "ceo"
    assert events[1]["aggregate_id"] == run_id


def test_event_stream_tails_live_events_until_terminal(client):
    """Exercises the live-tail branch directly (subscribe -> queue.get ->
    terminal-type break -> unsubscribe) without going through a real HTTP
    connection — asyncio.Queue isn't safe to drive across TestClient's
    background-thread event loop, so this is the reliable way to test the
    actual concurrency behavior. End-to-end live streaming can only be
    verified once the orchestration phase actually calls event_bus.publish().
    `client` is only used to get the moto-backed tables set up; the events
    table still needs to exist for the (empty) replay query at the top of
    event_stream()."""

    async def scenario() -> list[dict]:
        run_id = "run-live-test"
        received: list[dict] = []

        async def consume() -> None:
            async for chunk in event_stream(run_id, is_running=True):
                received.append(json.loads(chunk[len("data: ") :]))

        consumer = asyncio.create_task(consume())
        await asyncio.sleep(0.01)  # let the generator subscribe first

        event_bus.publish(run_id, {"type": "inception_started", "event_id": "e1"})
        await asyncio.sleep(0.01)
        event_bus.publish(run_id, {"type": "synthesis_completed", "event_id": "e2"})

        await asyncio.wait_for(consumer, timeout=1)
        return received

    received = asyncio.run(scenario())
    assert [e["type"] for e in received] == ["inception_started", "synthesis_completed"]
    assert event_bus._subscribers.get("run-live-test") in (None, [])


def test_event_stream_emits_keepalive_while_the_tail_is_silent(client, monkeypatch):
    """A live tail that goes quiet still has to put bytes on the wire.

    Cloudflare drops a proxied connection idle for 100s with a 524, and that
    ceiling is not raisable below Enterprise. A gap between two events is just
    an LLM call running long, so without a keepalive the stream dies partway
    through a deliberation. nginx never surfaced this -- proxy_read_timeout is
    3600s there -- so it only appears once a CDN sits in front.

    Reads _HEARTBEAT_SECONDS off the module rather than importing the value,
    so monkeypatch actually reaches the running generator.
    """
    monkeypatch.setattr(events_router, "_HEARTBEAT_SECONDS", 0.01)

    async def scenario() -> list[str]:
        run_id = "run-keepalive-test"
        chunks: list[str] = []

        async def consume() -> None:
            async for chunk in event_stream(run_id, is_running=True):
                chunks.append(chunk)

        consumer = asyncio.create_task(consume())
        # Several heartbeat intervals with nothing published.
        await asyncio.sleep(0.05)
        event_bus.publish(run_id, {"type": "synthesis_completed", "event_id": "e1"})

        await asyncio.wait_for(consumer, timeout=1)
        return chunks

    chunks = asyncio.run(scenario())

    assert ": keepalive\n\n" in chunks, "silent stretch produced no keepalive frame"
    # The real event still arrives, and still ends the stream.
    assert chunks[-1].startswith("data: ")
    assert json.loads(chunks[-1][len("data: ") :])["type"] == "synthesis_completed"
    assert event_bus._subscribers.get("run-keepalive-test") in (None, [])


def test_keepalive_frames_are_not_data_events(client, monkeypatch):
    """The comment frame must not reach the client as an event -- an SSE
    comment starts with ':' and carries no data field, so EventSource discards
    it. If it were ever emitted as `data:` the frontend would try to render a
    card for it."""
    monkeypatch.setattr(events_router, "_HEARTBEAT_SECONDS", 0.01)

    async def scenario() -> list[str]:
        run_id = "run-keepalive-shape"
        chunks: list[str] = []

        async def consume() -> None:
            async for chunk in event_stream(run_id, is_running=True):
                chunks.append(chunk)

        consumer = asyncio.create_task(consume())
        await asyncio.sleep(0.05)
        event_bus.publish(run_id, {"type": "error_occurred", "event_id": "e1"})
        await asyncio.wait_for(consumer, timeout=1)
        return chunks

    chunks = asyncio.run(scenario())
    keepalives = [c for c in chunks if not c.startswith("data: ")]

    assert keepalives, "expected at least one non-data frame"
    for frame in keepalives:
        assert frame.startswith(":"), f"keepalive must be an SSE comment, got {frame!r}"
    assert _sse_data_lines("".join(chunks)) == [{"type": "error_occurred", "event_id": "e1"}]
