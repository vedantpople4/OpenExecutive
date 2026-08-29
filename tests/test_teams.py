"""Tests for the hierarchical team deliberation feature (phase 2)."""

import dataclasses
import json
import threading
from datetime import datetime

import pytest
from unittest.mock import Mock, patch

from openexec.agents import TEAM_STRUCTURE, register_default_agents, registry
from openexec.agents.interface import AgentReport
from openexec.events import EventType
from openexec.orchestrator import Orchestrator, SimulationState
from openexec.ai.prompts import get_agent_system_prompt


class TestTeamStructure:
    """TEAM_STRUCTURE mapping correctness."""

    def test_team_structure_keys(self):
        assert set(TEAM_STRUCTURE.keys()) == {"ceo", "cfo", "cto", "cmo"}

    def test_team_members_present(self):
        for cxo, members in TEAM_STRUCTURE.items():
            for m in members:
                assert isinstance(m, str)
                assert m, f"Empty sub-role in {cxo}"
        assert len(TEAM_STRUCTURE["ceo"]) == 2
        assert len(TEAM_STRUCTURE["cfo"]) == 3
        assert len(TEAM_STRUCTURE["cto"]) == 3
        assert len(TEAM_STRUCTURE["cmo"]) == 3


class TestSubRoleRegistration:
    """AgentRegistry populates all sub-roles."""

    def test_sub_roles_registered(self):
        register_default_agents()
        expected = set()
        for members in TEAM_STRUCTURE.values():
            expected.update(members)
        for m in expected:
            assert m in registry.list_names(), f"{m} not registered"


class TestSubRolePrompts:
    """Each sub-role has a system prompt."""

    @pytest.mark.parametrize(
        "role",
        [
            "financial_analyst",
            "budget_planner",
            "risk_analyst",
            "engineering_lead",
            "solutions_architect",
            "sre",
            "growth_marketer",
            "content_strategist",
            "seo_specialist",
            "chief_of_staff",
            "strategy_associate",
        ],
    )
    def test_prompt_exists(self, role):
        prompt = get_agent_system_prompt(role)
        assert prompt and len(prompt) > 50


class TestTeamMemberFallback:
    """Team sub-agents must fail soft: retry the LLM, then a stub — never abort the run."""

    @pytest.fixture
    def stub_team_client(self):
        """TeamMemberTemplate builds a real AIClient in __init__, which reads a
        settings.json relative to the cwd. Without this the tests below pass only
        on a machine that happens to have one and fail on CI, which has none.

        templates_teams binds AIClient at import time, so the patch has to target
        that module's namespace rather than openexec.ai.client.
        """
        with patch("openexec.agents.templates_teams.AIClient"):
            yield

    def test_failed_analysis_returns_fallback_stub(self, stub_team_client):
        """A specialist whose LLM call throws returns is_fallback instead of raising."""
        from openexec.agents.templates_teams import TeamMemberTemplate

        member = TeamMemberTemplate("financial_analyst")
        state = SimulationState(core_prompt="test", assumptions={})
        state.data_corpus = {}
        with patch.object(member._ai_client, "complete_json_with_retry",
                          side_effect=RuntimeError("LLM down")):
            report = member.analyze(state)
        assert report.is_fallback is True
        assert report.alignment_score == 0.5

    def test_successful_analysis_not_fallback(self, stub_team_client):
        from openexec.agents.templates_teams import TeamMemberTemplate

        member = TeamMemberTemplate("financial_analyst")
        state = SimulationState(core_prompt="test", assumptions={})
        state.data_corpus = {}
        with patch.object(member._ai_client, "complete_json_with_retry",
                          return_value={"title": "T", "summary": "S"}):
            report = member.analyze(state)
        assert report.is_fallback is False


class TestOrchestratorTeamDeliberation:
    """Orchestrator.run() dispatches team deliberation when enabled."""

    def test_run_calls_team_deliberation_when_enabled(self):
        state = SimulationState(core_prompt="test")
        o = Orchestrator(registry)
        o.teams_enabled = True
        o.initialize(state)

        with patch.object(o, "run_inception") as m1, \
             patch.object(o, "run_analysis") as m2, \
             patch.object(o, "run_team_deliberation") as m3, \
             patch.object(o, "run_deliberation") as m4, \
             patch.object(o, "run_synthesis", return_value={}) as m5:
            o.run()

        m1.assert_called_once()
        m2.assert_called_once()
        m3.assert_called_once()
        m4.assert_called_once()
        m5.assert_called_once()

    def test_run_skips_team_deliberation_when_disabled(self):
        state = SimulationState(core_prompt="test")
        o = Orchestrator(registry)
        o.teams_enabled = False
        o.initialize(state)

        with patch.object(o, "run_inception") as m1, \
             patch.object(o, "run_analysis") as m2, \
             patch.object(o, "run_team_deliberation") as m3, \
             patch.object(o, "run_deliberation") as m4, \
             patch.object(o, "run_synthesis", return_value={}) as m5:
            o.run()

        m1.assert_called_once()
        m2.assert_called_once()
        m3.assert_not_called()
        m4.assert_called_once()
        m5.assert_called_once()

    def test_synthesize_team_position_called(self):
        """run_team_deliberation() invokes synthesize_team_position on CXO."""
        register_default_agents()
        backup = dict(registry._agents)  # save for restore
        try:
            state = SimulationState(core_prompt="test")
            o = Orchestrator(registry)
            o.initialize(state)

            # Mock ALL sub-agent returns (for all 4 teams)
            for cxo_name, members in TEAM_STRUCTURE.items():
                for member in members:
                    # A real AgentReport, not a Mock: run_team_deliberation now
                    # reads .title/.risks/.alignment_score into an event payload,
                    # and auto-Mock values are not JSON- or DynamoDB-safe.
                    m_report = AgentReport(title="t", summary="ok")
                    mock_member = Mock()
                    mock_member.analyze.return_value = m_report
                    registry._agents[member] = mock_member

            # Mock all CXO synthesize_team_position
            for cxo_name in TEAM_STRUCTURE:
                cxo_mock = Mock()
                cxo_mock.synthesize_team_position.return_value = AgentReport(
                    title="synth", summary="synth"
                )
                registry._agents[cxo_name] = cxo_mock

            o.run_team_deliberation()

            # All 4 CXOs should have synthesize_team_position called
            for cxo_name in TEAM_STRUCTURE:
                cxo_mock = registry._agents[cxo_name]
                cxo_mock.synthesize_team_position.assert_called_once()
        finally:
            registry._agents = backup


class TestTeamEventEmission:
    """Team mode used to make ~26 LLM calls and emit nothing, so the UI sat
    frozen. These assert the lifecycle events the frontend renders."""

    def _run_with_events(self, cancel_after=None):
        """Runs team deliberation against mocked agents, returning the emitted
        events. cancel_after: stop the run once N specialists have reported."""
        register_default_agents()
        backup = dict(registry._agents)
        try:
            state = SimulationState(core_prompt="test")
            state.active_agents = list(TEAM_STRUCTURE.keys())
            o = Orchestrator(registry)
            o.initialize(state)

            sink = Mock()
            emitted = []
            sink.append.side_effect = lambda e: emitted.append(e)
            o.set_event_store(sink)

            calls = {"n": 0}

            def make_member():
                member = Mock()

                def analyze(_state):
                    calls["n"] += 1
                    if cancel_after is not None and calls["n"] >= cancel_after:
                        state.cancel_event = threading.Event()
                        state.cancel_event.set()
                    return AgentReport(title="t", summary="ok")

                member.analyze.side_effect = analyze
                return member

            for _cxo, members in TEAM_STRUCTURE.items():
                for member_name in members:
                    registry._agents[member_name] = make_member()
            for cxo_name in TEAM_STRUCTURE:
                cxo_mock = Mock()
                cxo_mock.synthesize_team_position.return_value = AgentReport(title="s")
                registry._agents[cxo_name] = cxo_mock

            o.run_team_deliberation()
            return emitted
        finally:
            registry._agents = backup

    def _of_type(self, emitted, event_type):
        return [e for e in emitted if e.event_type == event_type]

    def test_emits_one_started_and_one_completed(self):
        emitted = self._run_with_events()
        assert len(self._of_type(emitted, EventType.TEAM_ANALYSIS_STARTED)) == 1
        assert len(self._of_type(emitted, EventType.TEAM_ANALYSIS_COMPLETED)) == 1

    def test_emits_a_specialist_report_per_member(self):
        emitted = self._run_with_events()
        reports = self._of_type(emitted, EventType.SPECIALIST_REPORT_GENERATED)
        expected = sum(len(members) for members in TEAM_STRUCTURE.values())
        assert len(reports) == expected

        for report in reports:
            assert report.parent_cxo, "a specialist report must name its CXO"
            assert report.agent_name in TEAM_STRUCTURE[report.parent_cxo]
            # 0 files the report under the team phase card, not a round.
            assert report.report_data["round_number"] == 0

    def test_speaking_precedes_each_specialist_report(self):
        emitted = self._run_with_events()
        relevant = [
            e for e in emitted
            if e.event_type in (EventType.AGENT_SPEAKING, EventType.SPECIALIST_REPORT_GENERATED)
        ]
        # Strictly alternating: speaking then report, per specialist. The
        # frontend clears the speaking indicator when the report arrives.
        for speaking, report in zip(relevant[::2], relevant[1::2]):
            assert speaking.event_type == EventType.AGENT_SPEAKING
            assert report.event_type == EventType.SPECIALIST_REPORT_GENERATED
            assert speaking.agent_name == report.agent_name

    def test_every_event_is_json_serializable(self):
        """Regression guard: a Mock report puts auto-Mock values into
        report_data that only blow up once they reach DynamoDB. Datetimes are
        the one non-primitive allowed -- anything else must raise here rather
        than in production."""
        def only_datetimes(value):
            if isinstance(value, datetime):
                return value.isoformat()
            raise TypeError(f"not JSON-safe: {type(value).__name__}")

        emitted = self._run_with_events()
        for event in emitted:
            json.dumps(dataclasses.asdict(event), default=only_datetimes)

    def test_completed_still_fires_when_cancelled_mid_run(self):
        emitted = self._run_with_events(cancel_after=1)
        assert len(self._of_type(emitted, EventType.TEAM_ANALYSIS_COMPLETED)) == 1
        # Cancellation cut the run short rather than running every team.
        reports = self._of_type(emitted, EventType.SPECIALIST_REPORT_GENERATED)
        assert len(reports) < sum(len(m) for m in TEAM_STRUCTURE.values())
