"""Estimate the LLM call count for a simulation before running it.

Reuses PHASE_ROUNDS and TEAM_STRUCTURE (the actual tables the orchestrator
runs on) instead of re-hardcoding round layout or team sizes, so this estimate
can't silently drift out of sync with real behavior.
"""

from typing import Iterable, Optional, Tuple

from openexec.agents import TEAM_STRUCTURE
from openexec.orchestrator_deliberation import PHASE_ROUNDS


def estimate_llm_calls(active_agents: Iterable[str], teams: bool) -> Tuple[int, int]:
    """Return (min_calls, max_calls) an `openexec run` with these settings
    will make.

    Deliberation length is inherently a range, not a fixed number -- it can
    converge as early as round 2 or 3, or always run through round 5 (round 5
    is a hard stop; round 6+ is unreachable regardless of max_rounds=10).
    """
    agents = {a.lower() for a in active_agents}
    non_ceo = [a for a in agents if a != "ceo"]

    # Phase 1: CEO inception.
    phase1 = 1 if "ceo" in agents else 0

    # Phase 2: blind analysis, one call per active non-CEO agent.
    phase2 = len(non_ceo)

    # Phase 2.5: --teams only. Each active CXO's specialists analyze, then
    # the CXO makes one more call to synthesize_team_position().
    phase2_5 = 0
    if teams:
        for cxo, specialists in TEAM_STRUCTURE.items():
            if cxo in agents:
                phase2_5 += len(specialists) + 1

    # Phase 3: deliberation. Count agent calls per round (filtered to active
    # agents) plus one Scribe call after any of rounds 2-4 that had
    # participants (rounds 1 and 5 never call the Scribe).
    round_counts = {
        round_num: len([a for a in participants if a in agents])
        for round_num, participants in PHASE_ROUNDS.items()
    }

    min_convergence_round = 2 if len(non_ceo) <= 1 else 3

    max_deliberation = round_counts.get(1, 0)
    for round_num in (2, 3, 4):
        count = round_counts.get(round_num, 0)
        max_deliberation += count
        if count > 0:
            max_deliberation += 1  # Scribe
    max_deliberation += round_counts.get(5, 0)  # CEO synthesis

    min_deliberation = round_counts.get(1, 0)
    for round_num in range(2, min_convergence_round):
        count = round_counts.get(round_num, 0)
        min_deliberation += count
        if count > 0:
            min_deliberation += 1  # Scribe
    min_deliberation += round_counts.get(5, 0)  # convergence-exit synthesis

    base = phase1 + phase2 + phase2_5
    return base + min_deliberation, base + max_deliberation


def estimate_cost(calls: int, price_per_call: Optional[float]) -> Optional[float]:
    """Estimate dollar cost for ``calls`` LLM calls.

    Returns None when no per-call price is configured (local inference, or the
    user hasn't set ``estimate.price_per_call``).
    """
    if price_per_call is None or price_per_call <= 0:
        return None
    return round(calls * price_per_call, 4)


def estimate_eta(calls: int, seconds_per_call: Optional[float]) -> Optional[str]:
    """Estimate wall-clock time for ``calls`` LLM calls.

    Returns None when no per-call latency is configured.
    """
    if seconds_per_call is None or seconds_per_call <= 0:
        return None
    seconds = round(calls * seconds_per_call)
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    remainder = seconds % 60
    if minutes < 60:
        return f"{minutes}m {remainder}s" if remainder else f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m" if mins else f"{hours}h"
