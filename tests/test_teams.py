"""Tests for the hierarchical team deliberation feature (phase 2)."""

import pytest
from unittest.mock import Mock, patch

from openexec.agents import TEAM_STRUCTURE, register_default_agents, registry
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
             patch.object(o, "run_review") as m4, \
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
             patch.object(o, "run_review") as m4, \
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
                    m_report = Mock(summary="ok", key_findings=[])
                    mock_member = Mock()
                    mock_member.analyze.return_value = m_report
                    registry._agents[member] = mock_member

            # Mock all CXO synthesize_team_position
            for cxo_name in TEAM_STRUCTURE:
                cxo_mock = Mock()
                cxo_mock.synthesize_team_position.return_value = Mock(
                    summary="synth", key_findings=[]
                )
                registry._agents[cxo_name] = cxo_mock

            o.run_team_deliberation()

            # All 4 CXOs should have synthesize_team_position called
            for cxo_name in TEAM_STRUCTURE:
                cxo_mock = registry._agents[cxo_name]
                cxo_mock.synthesize_team_position.assert_called_once()
        finally:
            registry._agents = backup
