"""Runs the openexec deliberation engine as a background task off a
POST /decisions request. See the plan's "LLM Orchestration Integration"
section for the full design (execution model, thread-safety, concurrency).
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from openexec.agents import DEFAULT_AGENTS, registry
from openexec.orchestrator import Orchestrator, SimulationState
from openexec.utils import extract_action_items

from app.repositories import decisions as decisions_repo
from app.services.orchestration_events import BackendEventSink

_main_loop: asyncio.AbstractEventLoop | None = None

# A single process-wide lock serializes deliberations. `registry` is a
# process-wide singleton of cached agent instances whose thread-safety under
# concurrent runs was never verified upstream — see the plan's concurrency
# rationale. threading.Lock (not asyncio.Lock): this runs in a plain OS
# thread via FastAPI's BackgroundTasks, never on the event loop.
_run_lock = threading.Lock()


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop


def get_main_loop() -> asyncio.AbstractEventLoop | None:
    return _main_loop


def run_deliberation(run_id: str, prompt: str, agents: list[str], team_mode_enabled: bool) -> None:
    """Sync, blocking — must only ever be invoked via FastAPI BackgroundTasks
    (runs in Starlette's thread pool), never awaited or scheduled on the
    event loop directly."""
    sink = BackendEventSink(run_id, get_main_loop())

    with _run_lock:
        try:
            state = SimulationState(
                simulation_id=run_id,
                core_prompt=prompt,
                decision_point=f"Decision required for: {prompt}",
                status="initialized",
            )
            state.active_agents = agents or list(DEFAULT_AGENTS)

            orchestrator = Orchestrator(registry, verbose=False)
            orchestrator.teams_enabled = team_mode_enabled
            orchestrator.set_event_store(sink)
            orchestrator.initialize(state)

            final_results: dict[str, Any] = orchestrator.run()
            action_items = extract_action_items(final_results)
            decisions_repo.complete_decision(run_id, final_results, action_items)
        except Exception as exc:
            # orchestrator.run() already emits an ErrorOccurred event itself
            # (via the same sink) before re-raising -- no duplicate event here.
            decisions_repo.fail_decision(run_id, str(exc))
