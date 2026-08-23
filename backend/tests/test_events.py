import asyncio
import json
from decimal import Decimal

from app.repositories import events as events_repo
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
