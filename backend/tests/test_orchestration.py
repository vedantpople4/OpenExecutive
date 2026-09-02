"""Backend plumbing around the openexec deliberation engine: repository
result-writing, the event sink adapter, and the run_deliberation background
task wrapper (including its concurrency lock). Deliberation-algorithm
correctness itself is already covered by openexec's own test suite (repo
root tests/test_orchestrator*.py) -- these tests only prove the backend's
wiring around it, so Orchestrator.run is monkeypatched throughout rather
than exercising real (or even fallback) agent logic."""

from __future__ import annotations

import asyncio
import threading
import time

from openexec.events import InceptionCompleted, SynthesisCompleted

from app.repositories import decisions as repo
from app.repositories import events as events_repo
from app.db import connection
from app.services import event_bus, orchestration
from app.services.orchestration_events import BackendEventSink
from tests.test_decisions import _submit


def _fake_final_results(**overrides):
    base = {
        "executive_summary": "Yes, proceed.",
        "decision_point": "Should we proceed?",
        "agent_reports": {"ceo": {"title": "CEO view", "alignment_score": 0.7}},
        # Integer round-number keys, exactly as openexec produces them
        # (SimulationState.deliberation_outputs is Dict[int, ...]) -- DynamoDB
        # map keys must be strings, so this shape is load-bearing here.
        "deliberation_rounds": {1: {"ceo": {"title": "R1", "alignment_score": 0.6}}},
        "board_decision": {"summary": "Go for it"},
        "overall_risk_assessment": ["Risk A", "Risk B", "Risk C", "Risk D"],
        "synthesized_recommendations": ["Do X"],
        "fallback_warnings": [],
    }
    base.update(overrides)
    return base


# -- complete_decision / fail_decision (repository layer) -------------------


def _seed_decision(run_id: str) -> None:
    """Events carry a foreign key to decisions now, so a synthetic run id
    needs its parent row before any event can land. Production always has
    one -- create_decision runs before the orchestrator emits anything."""
    with connection() as conn:
        conn.execute(
            "INSERT INTO decisions (id, status, prompt) VALUES (%s, 'running', 'seed')"
            " ON CONFLICT (id) DO NOTHING",
            (run_id,),
        )


def test_complete_decision_populates_result_fields(client):
    run_id = repo.create_decision("Should we expand?", ["ceo"], False, None)
    action_items = [{"description": "Hire regional lead", "owner": "cfo"}]

    repo.complete_decision(run_id, _fake_final_results(), action_items)

    item = repo.get_decision(run_id)
    assert item["status"] == "completed"
    assert item["executive_summary"] == "Yes, proceed."
    assert item["action_item_count"] == 1
    assert item["top_risks"] == ["Risk A", "Risk B", "Risk C"]
    assert item["agent_alignment"] == {"ceo": 0.7}
    assert item["agent_reports"]["ceo"]["alignment_score"] == 0.7
    # Round keys stringified for DynamoDB (see app/db.py) -- a live run
    # failed on exactly this before to_dynamodb_safe handled map keys.
    assert list(item["deliberation_rounds"].keys()) == ["1"]
    assert item["deliberation_rounds"]["1"]["ceo"]["alignment_score"] == 0.6


def test_complete_decision_is_noop_once_terminal(client):
    run_id = repo.create_decision("Should we expand?", ["ceo"], False, None)
    repo.stop_decision(run_id)

    repo.complete_decision(run_id, _fake_final_results(), [])

    item = repo.get_decision(run_id)
    assert item["status"] == "stopped"
    assert item.get("executive_summary") is None


def test_save_partial_decision_keeps_stopped_status(client):
    run_id = repo.create_decision("Should we expand?", ["ceo"], False, None)
    repo.stop_decision(run_id)

    repo.save_partial_decision(run_id, _fake_final_results(), [{"description": "do it"}])

    item = repo.get_decision(run_id)
    # The label survives, but the work the user paid for is kept.
    assert item["status"] == "stopped"
    assert item["executive_summary"] == "Yes, proceed."
    assert item["agent_reports"]["ceo"]["alignment_score"] == 0.7


def test_save_partial_decision_on_running_row_leaves_status(client):
    """Covers the race where the worker finishes before /stop's status write."""
    run_id = repo.create_decision("Should we expand?", ["ceo"], False, None)

    repo.save_partial_decision(run_id, _fake_final_results(), [])

    item = repo.get_decision(run_id)
    assert item["status"] == "running"
    assert item["executive_summary"] == "Yes, proceed."


def test_save_partial_decision_never_clobbers_a_finished_run(client):
    run_id = repo.create_decision("Should we expand?", ["ceo"], False, None)
    repo.complete_decision(run_id, _fake_final_results(executive_summary="Real result"), [])

    repo.save_partial_decision(run_id, _fake_final_results(executive_summary="Stale partial"), [])

    item = repo.get_decision(run_id)
    assert item["status"] == "completed"
    assert item["executive_summary"] == "Real result"


def test_fail_decision_sets_error_status(client):
    run_id = repo.create_decision("Should we expand?", ["ceo"], False, None)

    repo.fail_decision(run_id, "LLM provider unreachable")

    item = repo.get_decision(run_id)
    assert item["status"] == "error"
    assert item["error_message"] == "LLM provider unreachable"


def test_fail_decision_is_noop_once_terminal(client):
    run_id = repo.create_decision("Should we expand?", ["ceo"], False, None)
    repo.stop_decision(run_id)

    repo.fail_decision(run_id, "too late")

    assert repo.get_decision(run_id)["status"] == "stopped"


# -- BackendEventSink ---------------------------------------------------


def test_backend_event_sink_persists_nested_payload_shape(client):
    event = InceptionCompleted(event_id="e1", aggregate_id="run-sink-test", ceo_report={"title": "t"})
    _seed_decision("run-sink-test")
    sink = BackendEventSink("run-sink-test", loop=None)

    sink.append(event)

    stored = events_repo.list_events("run-sink-test")
    assert len(stored) == 1
    assert stored[0]["type"] == "inception_completed"
    assert stored[0]["payload"] == {"ceo_report": {"title": "t"}}
    assert stored[0]["aggregate_id"] == "run-sink-test"


def test_backend_event_sink_stringifies_int_map_keys_in_payload(client):
    """SynthesisCompleted carries the whole final_report, whose
    deliberation_rounds is keyed by int -- boto3 rejects non-string map keys,
    which killed a real run at the synthesis step before this was handled."""
    event = SynthesisCompleted(
        event_id="e3",
        aggregate_id="run-intkey-test",
        final_report={"deliberation_rounds": {1: {"ceo": {"alignment_score": 0.6}}}},
    )

    _seed_decision("run-intkey-test")
    BackendEventSink("run-intkey-test", loop=None).append(event)

    stored = events_repo.list_events("run-intkey-test")
    rounds = stored[0]["payload"]["final_report"]["deliberation_rounds"]
    assert list(rounds.keys()) == ["1"]
    assert rounds["1"]["ceo"]["alignment_score"] == 0.6


def test_backend_event_sink_publishes_flattened_live_event(client):
    # `client` only sets up moto + fake AWS creds (append_event still writes
    # to DynamoDB even on the live-publish path) -- same pattern as
    # test_events.py's live-tail test.
    async def scenario():
        loop = asyncio.get_running_loop()
        _seed_decision("run-live-sink-test")
        queue = event_bus.subscribe("run-live-sink-test")
        try:
            event = InceptionCompleted(
                event_id="e2", aggregate_id="run-live-sink-test", ceo_report={"title": "t"}
            )
            sink = BackendEventSink("run-live-sink-test", loop)
            # Real background thread, exactly like production -- proves the
            # call_soon_threadsafe bridge, not just a same-thread call.
            await asyncio.to_thread(sink.append, event)
            return await asyncio.wait_for(queue.get(), timeout=1)
        finally:
            event_bus.unsubscribe("run-live-sink-test", queue)

    received = asyncio.run(scenario())
    assert received["type"] == "inception_completed"
    assert received["ceo_report"] == {"title": "t"}
    assert received["aggregate_id"] == "run-live-sink-test"


# -- run_deliberation -----------------------------------------------------


def test_run_deliberation_completes_decision_on_success(client, monkeypatch):
    run_id = repo.create_decision("Should we launch?", ["ceo"], False, None)
    monkeypatch.setattr(orchestration.Orchestrator, "run", lambda self: _fake_final_results())
    monkeypatch.setattr(orchestration, "extract_action_items", lambda results: [{"description": "do it"}])

    orchestration.run_deliberation(run_id, "Should we launch?", ["ceo"], False)

    item = repo.get_decision(run_id)
    assert item["status"] == "completed"
    assert item["action_item_count"] == 1
    assert item["agent_alignment"] == {"ceo": 0.7}


def test_run_deliberation_fails_decision_on_exception(client, monkeypatch):
    run_id = repo.create_decision("Should we launch?", ["ceo"], False, None)

    def boom(self):
        raise RuntimeError("provider timeout")

    monkeypatch.setattr(orchestration.Orchestrator, "run", boom)

    orchestration.run_deliberation(run_id, "Should we launch?", ["ceo"], False)

    item = repo.get_decision(run_id)
    assert item["status"] == "error"
    assert item["error_message"] == "provider timeout"


def test_run_deliberation_serializes_concurrent_runs(client, monkeypatch):
    run_id_1 = repo.create_decision("First", ["ceo"], False, None)
    run_id_2 = repo.create_decision("Second", ["ceo"], False, None)

    def slow_run(self):
        time.sleep(0.2)
        return _fake_final_results()

    monkeypatch.setattr(orchestration.Orchestrator, "run", slow_run)
    monkeypatch.setattr(orchestration, "extract_action_items", lambda results: [])

    t1 = threading.Thread(target=orchestration.run_deliberation, args=(run_id_1, "First", ["ceo"], False))
    t1.start()
    time.sleep(0.05)  # let t1 acquire the lock first

    t2 = threading.Thread(target=orchestration.run_deliberation, args=(run_id_2, "Second", ["ceo"], False))
    t2.start()

    time.sleep(0.1)  # t1 is still sleeping (0.2s) -- t2 must still be blocked on the lock
    assert repo.get_decision(run_id_2)["status"] == "running"

    t1.join(timeout=2)
    t2.join(timeout=2)
    assert repo.get_decision(run_id_1)["status"] == "completed"
    assert repo.get_decision(run_id_2)["status"] == "completed"


# -- stop-race safety, end to end via HTTP --------------------------------


def test_request_cancel_returns_false_for_unknown_run(client):
    assert orchestration.request_cancel("run-not-running") is False


def test_cancel_registry_is_cleaned_up_after_success_and_failure(client, monkeypatch):
    monkeypatch.setattr(orchestration, "extract_action_items", lambda results: [])

    run_ok = repo.create_decision("ok", ["ceo"], False, None)
    monkeypatch.setattr(orchestration.Orchestrator, "run", lambda self: _fake_final_results())
    orchestration.run_deliberation(run_ok, "ok", ["ceo"], False)

    def boom(self):
        raise RuntimeError("provider timeout")

    run_bad = repo.create_decision("bad", ["ceo"], False, None)
    monkeypatch.setattr(orchestration.Orchestrator, "run", boom)
    orchestration.run_deliberation(run_bad, "bad", ["ceo"], False)

    assert orchestration._cancel_events == {}


def test_run_cancelled_while_queued_never_starts(client, monkeypatch):
    """A run waiting behind the process-wide lock must be cancellable before
    it burns a single LLM call."""
    run_id = repo.create_decision("Queued", ["ceo"], False, None)
    started = []
    monkeypatch.setattr(
        orchestration.Orchestrator, "run", lambda self: started.append(1) or _fake_final_results()
    )

    with orchestration._run_lock:
        worker = threading.Thread(
            target=orchestration.run_deliberation, args=(run_id, "Queued", ["ceo"], False)
        )
        worker.start()
        time.sleep(0.1)  # let it register and block on the lock
        assert orchestration.request_cancel(run_id) is True

    worker.join(timeout=2)
    assert started == []


def test_cancelled_mid_run_saves_partial_results(client, monkeypatch):
    run_id = repo.create_decision("Mid-run", ["ceo"], False, None)

    def cancel_then_return(self):
        # Stands in for the user hitting /stop while the engine is working.
        orchestration.request_cancel(run_id)
        return _fake_final_results()

    monkeypatch.setattr(orchestration.Orchestrator, "run", cancel_then_return)
    monkeypatch.setattr(orchestration, "extract_action_items", lambda results: [])

    orchestration.run_deliberation(run_id, "Mid-run", ["ceo"], False)

    item = repo.get_decision(run_id)
    # Not flipped to 'completed', but the work is preserved.
    assert item["status"] == "running"
    assert item["executive_summary"] == "Yes, proceed."


def test_stop_then_late_completion_does_not_resurrect_status(client, monkeypatch):
    monkeypatch.setattr(orchestration, "run_deliberation", lambda *args, **kwargs: None)
    run_id = _submit(client, "Should we launch?").json()["runId"]

    client.post(f"/decisions/{run_id}/stop")
    # Simulates the background thread finishing its (real) run after the
    # stop request already won the race.
    repo.complete_decision(run_id, _fake_final_results(), [])

    assert repo.get_decision(run_id)["status"] == "stopped"
