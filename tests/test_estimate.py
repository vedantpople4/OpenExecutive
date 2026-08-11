"""Tests for the dry-run call estimate — must stay in sync with the
orchestrator's actual round/team layout (the "can't silently drift" claim)."""

import pytest

from openexec.agents import TEAM_STRUCTURE
from openexec.estimate import estimate_cost, estimate_eta, estimate_llm_calls
from openexec.orchestrator_deliberation import PHASE_ROUNDS


def _real_max_calls(active_agents, teams):
    """Independent recomputation from the data tables, mirroring estimate.

    Used as an oracle: this is a second implementation, so a drift between
    estimate_llm_calls and this function means one of them fell out of sync
    with PHASE_ROUNDS / TEAM_STRUCTURE.
    """
    agents = {a.lower() for a in active_agents}
    non_ceo = [a for a in agents if a != "ceo"]

    calls = 1 if "ceo" in agents else 0  # inception
    calls += len(non_ceo)  # phase-2 blind analysis
    if teams:
        for cxo, specialists in TEAM_STRUCTURE.items():
            if cxo in agents:
                calls += len(specialists) + 1  # specialists + CXO synthesis
    for rnd, participants in PHASE_ROUNDS.items():
        count = len([a for a in participants if a in agents])
        calls += count
        if rnd in (2, 3, 4) and count > 0:
            calls += 1  # Scribe
    return calls


@pytest.mark.parametrize("agents,teams", [
    (["ceo", "cfo", "cto", "cmo"], False),
    (["ceo", "cfo", "cto", "cmo"], True),
    (["cfo", "cto"], False),
    (["cfo", "cto"], True),
    (["cmo"], False),
    (["ceo"], False),
])
def test_estimate_max_matches_oracle(agents, teams):
    _min, max_calls = estimate_llm_calls(agents, teams)
    assert max_calls == _real_max_calls(agents, teams)


def test_estimate_floor_does_not_exceed_ceiling():
    for agents in (["ceo", "cfo", "cto", "cmo"], ["cfo", "cto"], ["ceo"]):
        for teams in (False, True):
            lo, hi = estimate_llm_calls(agents, teams)
            assert lo <= hi


def test_estimate_uses_all_phase_rounds():
    # Every round's participant layout must factor into the estimate.
    lo, hi = estimate_llm_calls(["ceo", "cfo", "cto", "cmo"], False)
    assert hi >= sum(len(p) for p in PHASE_ROUNDS.values())


class TestEstimateCost:
    def test_priced_cost(self):
        assert estimate_cost(10, 0.01) == 0.1

    def test_none_when_unpriced(self):
        assert estimate_cost(10, None) is None
        assert estimate_cost(10, 0) is None
        assert estimate_cost(10, -1) is None

    def test_rounding(self):
        assert estimate_cost(3, 0.001) == 0.003


class TestEstimateEta:
    def test_seconds_only_below_minute(self):
        assert estimate_eta(3, 10) == "30s"

    def test_minutes(self):
        assert estimate_eta(6, 20) == "2m"

    def test_minutes_with_remainder(self):
        assert estimate_eta(5, 20) == "1m 40s"

    def test_hours_format(self):
        eta = estimate_eta(200, 20)  # 4000s = 66m
        assert eta == "1h 6m"

    def test_hours_exact(self):
        assert estimate_eta(180, 20) == "1h"

    def test_none_when_no_latency(self):
        assert estimate_eta(10, None) is None
        assert estimate_eta(10, 0) is None