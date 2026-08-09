"""Fallback integrity: a failed model call must produce is_fallback=True and
those stub reports must be excluded from synthesized outputs downstream."""

from unittest.mock import Mock, patch

from openexec.orchestrator import SimulationState
from openexec.agents.templates_base import AgentTemplate


class _Dummy(AgentTemplate):
    name = "ceo"
    role = "Chief Executive Officer"
    fallback_title = "Dummy Report"
    fallback_alignment = 0.5
    fallback_focus_areas = ["Vision"]
    fallback_recommendations = ["placeholder rec"]
    fallback_risks = ["placeholder risk"]

    def _fallback_summary(self, state):
        return "dummy summary"

    def _fallback_findings(self, state):
        return ["dummy finding"]


def _state():
    s = SimulationState(core_prompt="test", assumptions={})
    s.data_corpus = {}
    return s


class TestFallbackReporting:
    def test_failed_analysis_produces_fallback(self):
        agent = _Dummy()
        with patch.object(agent.ai_client, "complete_json_with_retry",
                          side_effect=RuntimeError("LLM down")):
            report = agent.analyze(_state())
        assert report.is_fallback is True
        assert report.alignment_score == 0.5

    def test_successful_analysis_not_fallback(self):
        agent = _Dummy()
        with patch.object(agent.ai_client, "complete_json_with_retry",
                          return_value={"title": "T", "summary": "S"}):
            report = agent.analyze(_state())
        assert report.is_fallback is False

    def test_fallback_excluded_from_synthesized_recommendations(self):
        from openexec.orchestrator import Orchestrator
        from openexec.agents.interface import AgentReport

        class _FailAgent(AgentTemplate):
            name = "ceo"
            role = "c"
            fallback_title = "t"
            def _fallback_summary(self, s): return "s"
            def _fallback_findings(self, s): return []

        orch = Orchestrator(Mock())
        state = _state()
        state.agent_outputs = {
            "ceo": _FailAgent()._build_fallback_report(state),
            "cfo": AgentReport(
                title="real", summary="s", key_findings=[],
                recommendations=["REAL ACTION"], risks=["r"], alignment_score=0.8,
            ),
        }
        orch.state = state
        recs = orch._synthesize_recommendations()
        assert not any("placeholder" in r for r in recs)
        assert any("REAL ACTION" in r for r in recs)

    def test_fallback_excluded_from_synthesized_risks(self):
        from openexec.orchestrator import Orchestrator
        from openexec.agents.interface import AgentReport

        class _FailAgent(AgentTemplate):
            name = "ceo"
            role = "c"
            fallback_title = "t"
            def _fallback_summary(self, s): return "s"
            def _fallback_findings(self, s): return []

        orch = Orchestrator(Mock())
        state = _state()
        state.agent_outputs = {
            "ceo": _FailAgent()._build_fallback_report(state),
            "cfo": AgentReport(
                title="real", summary="s", key_findings=[],
                recommendations=["r"], risks=["REAL RISK"], alignment_score=0.8,
            ),
        }
        orch.state = state
        risks = orch._synthesize_risks()
        assert not any("placeholder" in r for r in risks)
        assert any("REAL RISK" in r for r in risks)