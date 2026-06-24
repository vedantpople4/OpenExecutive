"""Tests for recent changes in orchestrator_deliberation.py and orchestrator.py.

Covers:
- DeliberationOrchestrator verbose flag
- _dump_agent_report verbose helper
- Agent weight tagging in _synthesize_recommendations / _synthesize_risks
- _report_to_dict and _reports_to_dicts helpers
- _hardcoded_deliberation_report fallback
- _consolidate_challenges
- PHASE_ROUNDS constant
- Dead-code regression (lines after return in _reports_to_dicts)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from io import StringIO

from openexec.orchestrator_deliberation import DeliberationOrchestrator, PHASE_ROUNDS
from openexec.orchestrator import Orchestrator, SimulationState
from openexec.agents.interface import AgentReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_report(**overrides):
    """Build a minimal AgentReport-like mock."""
    defaults = dict(
        title="T", summary="S", key_findings=["f1"],
        recommendations=["r1"], risks=["rk1"],
        alignment_score=0.5, round_number=1,
        position=None, required_changes=[],
        challenges_for={}, challenges_for_cfo=[],
        challenges_for_cto=[], challenges_for_cmo=[],
        decision=None, consensus_statement=None,
        consensus_points=None, final_actions=None,
        contingencies=None, board_decision=None,
    )
    defaults.update(overrides)
    report = Mock(**defaults)
    report.get_role_specific_fields.return_value = {}
    return report


def _make_state(**overrides):
    defaults = dict(
        core_prompt="test prompt",
        decision_point="Decision required for: test prompt",
        status="initialized",
        agent_outputs={},
        challenges={"cfo": [], "cto": [], "cmo": []},
        deliberation_outputs={},
        deliberation_round=0,
        board_summary="",
        agent_weights={},
        data_corpus={},
        errors=[],
        phase="",
        simulation_id="test-id",
    )
    defaults.update(overrides)
    state = Mock(**defaults)
    return state


# ---------------------------------------------------------------------------
# PHASE_ROUNDS constant
# ---------------------------------------------------------------------------

class TestPhaseRounds:
    def test_round_count(self):
        assert len(PHASE_ROUNDS) == 5

    def test_round1_ceo(self):
        assert PHASE_ROUNDS[1] == ("ceo",)

    def test_round5_ceo(self):
        assert PHASE_ROUNDS[5] == ("ceo",)

    def test_round2_cfo_cto(self):
        assert set(PHASE_ROUNDS[2]) == {"cfo", "cto"}

    def test_round3_cmo(self):
        assert PHASE_ROUNDS[3] == ("cmo",)

    def test_round4_multi(self):
        assert set(PHASE_ROUNDS[4]) == {"cfo", "cto", "cmo"}


# ---------------------------------------------------------------------------
# DeliberationOrchestrator initialization
# ---------------------------------------------------------------------------

class TestDeliberationOrchestratorInit:

    def test_default_verbose_false(self):
        orch = DeliberationOrchestrator(Mock(), Mock())
        assert orch.verbose is False

    def test_verbose_true(self):
        orch = DeliberationOrchestrator(Mock(), Mock(), verbose=True)
        assert orch.verbose is True

    def test_ai_clients_empty_on_init(self):
        orch = DeliberationOrchestrator(Mock(), Mock())
        assert orch._ai_clients == {}


# ---------------------------------------------------------------------------
# _dump_agent_report
# ---------------------------------------------------------------------------

class TestDumpAgentReport:

    def test_prints_summary(self, capsys):
        orch = DeliberationOrchestrator(_make_state(), Mock(), verbose=True)
        report = _make_report(summary="board consensus")
        orch._dump_agent_report("ceo", 1, report)
        out = capsys.readouterr().out
        assert "board consensus" in out

    def test_prints_position(self, capsys):
        report = _make_report(position="bullish")
        orch = DeliberationOrchestrator(_make_state(), Mock(), verbose=True)
        orch._dump_agent_report("cfo", 2, report)
        out = capsys.readouterr().out
        assert "bullish" in out

    def test_prints_required_changes(self, capsys):
        report = _make_report(required_changes=["change XYZ"])
        orch = DeliberationOrchestrator(_make_state(), Mock(), verbose=True)
        orch._dump_agent_report("cto", 2, report)
        out = capsys.readouterr().out
        assert "change XYZ" in out

    def test_prints_risks(self, capsys):
        report = _make_report(risks=["cash burn"])
        orch = DeliberationOrchestrator(_make_state(), Mock(), verbose=True)
        orch._dump_agent_report("cfo", 2, report)
        out = capsys.readouterr().out
        assert "cash burn" in out

    def test_prints_key_findings(self, capsys):
        report = _make_report(key_findings=["GPU shortage"])
        orch = DeliberationOrchestrator(_make_state(), Mock(), verbose=True)
        orch._dump_agent_report("cto", 2, report)
        out = capsys.readouterr().out
        assert "GPU shortage" in out

    def test_prints_challenges_for(self, capsys):
        report = _make_report(challenges_for={"cfo": ["justify runway"]})
        orch = DeliberationOrchestrator(_make_state(), Mock(), verbose=True)
        orch._dump_agent_report("ceo", 1, report)
        out = capsys.readouterr().out
        assert "justify runway" in out

    def test_prints_decision_field(self, capsys):
        report = _make_report(decision="Approve")
        orch = DeliberationOrchestrator(_make_state(), Mock(), verbose=True)
        orch._dump_agent_report("ceo", 5, report)
        out = capsys.readouterr().out
        assert "Approve" in out

    def test_prints_consensus_points_list(self, capsys):
        report = _make_report(consensus_points=["point A", "point B"])
        orch = DeliberationOrchestrator(_make_state(), Mock(), verbose=True)
        orch._dump_agent_report("ceo", 5, report)
        out = capsys.readouterr().out
        assert "point A" in out
        assert "point B" in out

    def test_skips_none_fields(self, capsys):
        report = _make_report(summary=None, decision=None)
        orch = DeliberationOrchestrator(_make_state(), Mock(), verbose=True)
        orch._dump_agent_report("ceo", 1, report)
        out = capsys.readouterr().out
        # Should not crash; CEO header still prints
        assert "CEO" in out

    def test_cmo_header_color(self, capsys):
        report = _make_report(summary="market shift")
        orch = DeliberationOrchestrator(_make_state(), Mock(), verbose=True)
        orch._dump_agent_report("cmo", 3, report)
        out = capsys.readouterr().out
        assert "CMO" in out


# ---------------------------------------------------------------------------
# _hardcoded_deliberation_report
# ---------------------------------------------------------------------------

class TestHardcodedFallback:

    @pytest.mark.parametrize("round_num,expected_summary_fragment", [
        (1, "frames board"),
        (2, "responds to"),
        (3, "CMO raises"),
        (4, "revises position"),
        (5, "synthesizes board decision"),
    ])
    def test_fallback_per_round(self, round_num, expected_summary_fragment):
        orch = DeliberationOrchestrator(_make_state(), Mock())
        report = orch._hardcoded_deliberation_report("cfo", round_num)
        assert expected_summary_fragment in report.summary
        assert report.round_number == round_num
        assert report.alignment_score == 0.5

    def test_fallback_title(self):
        orch = DeliberationOrchestrator(_make_state(), Mock())
        report = orch._hardcoded_deliberation_report("cto", 2)
        assert "CTO" in report.title
        assert "Round 2" in report.title


# ---------------------------------------------------------------------------
# _consolidate_challenges
# ---------------------------------------------------------------------------

class TestConsolidateChallenges:

    def test_extracts_cfo_challenges(self):
        ceo_report = _make_report(
            challenges_for_cfo=["quantify runway"],
            challenges_for_cto=["feasibility check"],
            challenges_for_cmo=["market signal"],
        )
        state = _make_state(challenges={"cfo": [], "cto": [], "cmo": []})
        orch = DeliberationOrchestrator(state, Mock())
        orch._consolidate_challenges(1, {"ceo": ceo_report})
        assert state.challenges["cfo"] == ["quantify runway"]
        assert state.challenges["cto"] == ["feasibility check"]
        assert state.challenges["cmo"] == ["market signal"]

    def test_no_ceo_report_noop(self):
        state = _make_state(challenges={"cfo": [], "cto": [], "cmo": []})
        orch = DeliberationOrchestrator(state, Mock())
        orch._consolidate_challenges(1, {})
        assert state.challenges["cfo"] == []

    def test_empty_challenges(self):
        ceo_report = _make_report(
            challenges_for_cfo=[], challenges_for_cto=[], challenges_for_cmo=[]
        )
        state = _make_state(challenges={"cfo": [], "cto": [], "cmo": []})
        orch = DeliberationOrchestrator(state, Mock())
        orch._consolidate_challenges(1, {"ceo": ceo_report})
        assert state.challenges["cfo"] == []


# ---------------------------------------------------------------------------
# _report_to_dict / _reports_to_dicts
# ---------------------------------------------------------------------------

class TestReportToDict:

    def test_includes_core_fields(self):
        orch = DeliberationOrchestrator(_make_state(), Mock())
        report = AgentReport(
            title="T", summary="S", key_findings=["f"],
            recommendations=["r"], risks=["rk"],
            alignment_score=0.8, round_number=3,
        )
        d = orch._report_to_dict(report)
        assert d["title"] == "T"
        assert d["summary"] == "S"
        assert d["key_findings"] == ["f"]
        assert d["alignment_score"] == 0.8

    def test_includes_role_specific(self):
        report = AgentReport(
            title="T", summary="S", capex_vs_opex="CapEx",
            key_findings=[], recommendations=[], risks=[],
        )
        orch = DeliberationOrchestrator(_make_state(), Mock())
        d = orch._report_to_dict(report)
        assert d["capex_vs_opex"] == "CapEx"


class TestReportsToDicts:

    def test_converts_agent_reports(self):
        orch = DeliberationOrchestrator(_make_state(), Mock())
        report = AgentReport(title="R1", summary="S", key_findings=["f"],
                             recommendations=["r"], risks=["rk"], alignment_score=0.8,
                             round_number=1)
        outputs = {1: {"ceo": report}}
        result = orch._reports_to_dicts(outputs)
        assert result[1]["ceo"]["title"] == "R1"

    def test_passes_through_dicts(self):
        orch = DeliberationOrchestrator(_make_state(), Mock())
        outputs = {0: {"ceo": {"title": "already-dict"}}}
        result = orch._reports_to_dicts(outputs)
        assert result[0]["ceo"]["title"] == "already-dict"

    def test_no_dead_code_regression(self):
        """_reports_to_dicts used to have dead code after its return.
        Verify the method still works correctly after cleanup."""
        orch = DeliberationOrchestrator(_make_state(), Mock())
        report = AgentReport(title="clean", summary="S", key_findings=[],
                             recommendations=[], risks=[], alignment_score=0.5,
                             round_number=1)
        result = orch._reports_to_dicts({1: {"ceo": report}})
        assert "clean" in result[1]["ceo"]["title"]


# ---------------------------------------------------------------------------
# Agent weight tagging in Orchestrator._synthesize_recommendations / _synthesize_risks
# ---------------------------------------------------------------------------

class TestSynthesizeRecommendationsWeightTagging:

    def _make_orchestrator_with_reports(self, weights=None):
        from openexec.agents.interface import AgentReport
        reg = Mock()
        reg.list_names.return_value = ["ceo", "cfo"]
        orch = Orchestrator(reg)
        state = SimulationState(core_prompt="test")
        state.agent_weights = weights or {}
        state.agent_outputs = {
            "ceo": AgentReport(
                title="CEO Report", summary="s",
                key_findings=[], recommendations=["expand to EU"],
                risks=["market risk"], alignment_score=0.7,
            ),
            "cfo": AgentReport(
                title="CFO Report", summary="s",
                key_findings=[], recommendations=["preserve cash"],
                risks=["runway risk"], alignment_score=0.6,
            ),
        }
        orch.state = state
        return orch

    def test_default_weight_no_tag(self):
        orch = self._make_orchestrator_with_reports()
        recs = orch._synthesize_recommendations()
        ceo_recs = [r for r in recs if r.startswith("[CEO]")]
        assert len(ceo_recs) == 1
        assert "[W:" not in ceo_recs[0]

    def test_weight_below_1_tagged(self):
        orch = self._make_orchestrator_with_reports(weights={"cfo": 0.5})
        recs = orch._synthesize_recommendations()
        cfo_recs = [r for r in recs if "[CFO]" in r]
        assert any("[W:0.5]" in r for r in cfo_recs)

    def test_weight_1_not_tagged(self):
        orch = self._make_orchestrator_with_reports(weights={"cfo": 1.0})
        recs = orch._synthesize_recommendations()
        cfo_recs = [r for r in recs if "[CFO]" in r]
        assert all("[W:" not in r for r in cfo_recs)

    def test_ceo_weight_0_8_tagged(self):
        orch = self._make_orchestrator_with_reports(weights={"ceo": 0.8})
        recs = orch._synthesize_recommendations()
        ceo_recs = [r for r in recs if "[CEO]" in r]
        assert any("[W:0.8]" in r for r in ceo_recs)


class TestSynthesizeRisksWeightTagging:

    def _make_orchestrator_with_risks(self, weights=None):
        from openexec.agents.interface import AgentReport
        reg = Mock()
        reg.list_names.return_value = ["ceo", "cfo"]
        orch = Orchestrator(reg)
        state = SimulationState(core_prompt="test")
        state.agent_weights = weights or {}
        state.agent_outputs = {
            "ceo": AgentReport(
                title="CEO", summary="s",
                key_findings=[], recommendations=[],
                risks=["reputational risk"], alignment_score=0.7,
            ),
            "cfo": AgentReport(
                title="CFO", summary="s",
                key_findings=[], recommendations=[],
                risks=["liquidity crunch"], alignment_score=0.6,
            ),
        }
        orch.state = state
        return orch

    def test_default_no_weight_tag(self):
        orch = self._make_orchestrator_with_risks()
        risks = orch._synthesize_risks()
        cfo_risks = [r for r in risks if "[CFO]" in r]
        assert all("[W:" not in r for r in cfo_risks)

    def test_weight_below_1_tagged(self):
        orch = self._make_orchestrator_with_risks(weights={"cfo": 0.3})
        risks = orch._synthesize_risks()
        cfo_risks = [r for r in risks if "[CFO]" in r]
        assert any("[W:0.3]" in r for r in cfo_risks)


# ---------------------------------------------------------------------------
# SimulationState.agent_weights
# ---------------------------------------------------------------------------

class TestSimulationStateWeights:

    def test_default_empty(self):
        state = SimulationState(core_prompt="test")
        assert state.agent_weights == {}

    def test_set_weights(self):
        state = SimulationState(
            core_prompt="test",
            agent_weights={"cfo": 0.5, "cto": 0.8},
        )
        assert state.agent_weights["cfo"] == 0.5
        assert state.agent_weights["cto"] == 0.8


# ---------------------------------------------------------------------------
# Verbose output in run_deliberation loop
# ---------------------------------------------------------------------------

class TestVerboseRunDeliberation:

    @patch.object(DeliberationOrchestrator, "_init_ai_clients")
    @patch.object(DeliberationOrchestrator, "_call_agent")
    @patch.object(DeliberationOrchestrator, "_update_board_summary")
    @patch("openexec.ai.build_deliberation_prompt")
    def test_verbose_prints_agents_this_round(self, mock_bdp, mock_update, mock_call, mock_init, capsys):
        report = _make_report(summary="verbose test")
        mock_call.return_value = report
        state = _make_state()
        state.agent_outputs = {"ceo": _make_report(title="CEO blind")}
        orch = DeliberationOrchestrator(state, Mock(), verbose=True)
        orch.run_deliberation()
        out = capsys.readouterr().out
        assert "agents this round" in out

    @patch.object(DeliberationOrchestrator, "_init_ai_clients")
    @patch.object(DeliberationOrchestrator, "_call_agent")
    @patch.object(DeliberationOrchestrator, "_update_board_summary")
    @patch("openexec.ai.build_deliberation_prompt")
    def test_non_verbose_no_agent_detail(self, mock_bdp, mock_update, mock_call, mock_init, capsys):
        report = _make_report(summary="quiet test")
        mock_call.return_value = report
        state = _make_state()
        state.agent_outputs = {"ceo": _make_report(title="CEO blind")}
        orch = DeliberationOrchestrator(state, Mock(), verbose=False)
        orch.run_deliberation()
        out = capsys.readouterr().out
        assert "agents this round" not in out
