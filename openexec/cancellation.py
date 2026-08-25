"""Cooperative cancellation for a running simulation.

A caller that wants to be able to stop a run attaches a `threading.Event` to
the SimulationState as `cancel_event`; the phase loops check it between units
of work. The CLI attaches nothing, so every check is a no-op there.

Cancellation is NOT immediate. The AI providers use blocking `requests` calls
with no interrupt handle, so a check only lands between LLM calls -- expect
one call's latency (typically 10-60s, up to the configured timeout).
"""

from typing import Any


def is_cancelled(state: Any) -> bool:
    """True only when a real, set Event is attached.

    The `is True` comparison is load-bearing rather than pedantic: tests
    construct orchestrators with `Mock()` states, and `Mock().is_set()`
    returns a truthy Mock, which would otherwise cancel every mocked run.
    """
    event = getattr(state, "cancel_event", None)
    is_set = getattr(event, "is_set", None)
    return callable(is_set) and is_set() is True
