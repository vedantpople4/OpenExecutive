"""Tests for openexec/orchestrator.py — SimulationState and Orchestrator."""

import pytest
from unittest.mock import Mock, patch
from openexec.orchestrator import SimulationState


class TestSimulationState:
    """SimulationState dataclass."""

    def test_initialization(self):
        """Basic SimulationState creation."""
        state = SimulationState(
            core_prompt="Test decision",
            data_corpus={"doc1.md": "content"}
        )
        assert state.core_prompt == "Test decision"
        assert state.data_corpus["doc1.md"] == "content"
        assert state.status == "idle"
        assert state.deliberation_round == 0
        assert state.deliberation_outputs == {}

    def test_default_fields(self):
        """Default field values are correct."""
        state = SimulationState(core_prompt="Test")
        assert state.status == "idle"
        assert state.phase == ""
        assert state.agent_outputs == {}
        assert state.errors == []
        assert state.deliberation_round == 0
        assert state.challenges == {}
        assert state.deliberation_outputs == {}
        assert state.active_agents == []

    def test_deliberation_fields(self):
        """Deliberation-specific fields are present."""
        state = SimulationState(core_prompt="Test")
        assert hasattr(state, 'deliberation_round')
        assert hasattr(state, 'challenges')
        assert hasattr(state, 'deliberation_outputs')
        assert hasattr(state, 'active_agents')
        # These should start empty/defaulted
        assert state.deliberation_round == 0
        assert state.challenges == {}
        assert state.deliberation_outputs == {}
        assert state.active_agents == []


class TestOrchestrator:
    """Orchestrator class tests."""

    @pytest.fixture
    def mock_registry(self):
        """Mock agent registry for testing."""
        mock = Mock()
        mock.list_names.return_value = ["ceo", "cfo", "cto", "cmo"]
        return mock

    @pytest.fixture
    def orchestrator(self, mock_registry):
        """Create a minimal orchestrator for testing."""
        from openexec.orchestrator import Orchestrator
        orch = Orchestrator(mock_registry)
        return orch

    def test_initialization(self, orchestrator):
        """Orchestrator initializes correctly."""
        assert orchestrator.registry is not None
        assert orchestrator.state is None

    def test_initialize_sets_state(self, orchestrator, simulation_state):
        """initialize() sets the state correctly."""
        orchestrator.initialize(simulation_state)
        assert orchestrator.state == simulation_state

    def test_run_methods_exist(self, orchestrator):
        """All required methods are present."""
        assert hasattr(orchestrator, 'run_inception')
        assert hasattr(orchestrator, 'run_analysis')
        assert hasattr(orchestrator, 'run_review')
        assert hasattr(orchestrator, 'run_synthesis')

    def test_run_inception_calls_ceo(self, orchestrator, simulation_state):
        """run_inception() delegates to CEO."""
        orchestrator.initialize(simulation_state)
        with patch.object(orchestrator.registry, 'get') as mock_get:
            mock_agent = Mock()
            mock_get.return_value = mock_agent
            orchestrator.run_inception()
            mock_get.assert_called_with("ceo")
            mock_agent.analyze.assert_called()  # assuming analyze is called on the agent

    def test_run_review_calls_deliberation(self, orchestrator, simulation_state):
        """run_review() should delegate to run_deliberation()."""
        orchestrator.state = simulation_state
        with patch.object(orchestrator, 'run_deliberation') as mock_deliberation:
            orchestrator.run_review()
            mock_deliberation.assert_called_once()

    def test_run_analysis_filters_agents(self, orchestrator, mock_registry):
        """run_analysis() only calls agents in active_agents list."""
        from openexec.orchestrator import SimulationState
        state = SimulationState(
            core_prompt="Test",
            active_agents=["ceo", "cmo"]  # Only CEO and CMO active
        )
        orchestrator.initialize(state)

        # Mock agents
        agents = {
            "ceo": Mock(),
            "cfo": Mock(),
            "cto": Mock(),
            "cmo": Mock(),
        }
        mock_registry.get.side_effect = lambda name: agents.get(name)

        orchestrator.run_analysis()

        # CEO is skipped in run_analysis loop (line 133)
        # Only CMO should be called
        agents["cmo"].analyze.assert_called()
        agents["cfo"].analyze.assert_not_called()
        agents["cto"].analyze.assert_not_called()

    def test_run_review_calls_deliberation(self, orchestrator, simulation_state):
        """run_review() should delegate to run_deliberation()."""
        orchestrator.state = simulation_state
        with patch.object(orchestrator, 'run_deliberation') as mock_deliberation:
            orchestrator.run_review()
            mock_deliberation.assert_called_once()

    def test_run_deliberation_exists(self, orchestrator):
        """Deliberation method exists and can be called."""
        assert hasattr(orchestrator, 'run_deliberation')
        # We can't test the actual method without a full setup, but we can check it exists
        assert callable(getattr(orchestrator, 'run_deliberation', None))