"""Tests for openexec/orchestrator.py — SimulationState and Orchestrator."""

import threading

import pytest
from unittest.mock import Mock, patch
from openexec.orchestrator import Orchestrator, SimulationState


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
        assert hasattr(orchestrator, 'run_deliberation')
        assert hasattr(orchestrator, 'run_synthesis')

    def test_run_inception_calls_ceo(self, orchestrator, simulation_state):
        """run_inception() delegates to CEO when CEO is active."""
        orchestrator.initialize(simulation_state)
        orchestrator.state.active_agents = ["ceo"]
        with patch.object(orchestrator.registry, 'get') as mock_get:
            mock_agent = Mock()
            mock_get.return_value = mock_agent
            orchestrator.run_inception()
            mock_get.assert_called_with("ceo")
            mock_agent.analyze.assert_called()  # assuming analyze is called on the agent

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

    def test_run_call_deliberation(self, orchestrator, simulation_state):
        """run() invokes run_deliberation()."""
        orchestrator.state = simulation_state
        with patch.object(orchestrator, 'run_inception'), \
             patch.object(orchestrator, 'run_analysis'), \
             patch.object(orchestrator, 'run_deliberation') as mock_deliberation, \
             patch.object(orchestrator, 'run_synthesis', return_value={}):
            orchestrator.run()
            mock_deliberation.assert_called_once()

    def test_run_deliberation_exists(self, orchestrator):
        """Deliberation method exists and can be called."""
        assert hasattr(orchestrator, 'run_deliberation')
        # We can't test the actual method without a full setup, but we can check it exists
        assert callable(getattr(orchestrator, 'run_deliberation', None))

class TestCancellation:
    """Cooperative cancellation (openexec.cancellation). The engine must stop
    between units of work, keep whatever it already produced, and stay
    completely inert for callers that never attach an event -- i.e. the CLI."""

    def _state(self, cancel_event=None):
        state = SimulationState(core_prompt="Should we expand?", decision_point="Expand?")
        state.active_agents = ["ceo", "cfo", "cto", "cmo"]
        if cancel_event is not None:
            state.cancel_event = cancel_event
        return state

    def _registry(self, calls):
        def make_agent(name):
            agent = Mock()
            agent.analyze.side_effect = lambda state, n=name: calls.append(n) or Mock(
                title="t", summary="s", key_findings=[], recommendations=[], risks=[],
                alignment_score=0.8, get_role_specific_fields=lambda: {},
            )
            return agent

        registry = Mock()
        registry.list_names.return_value = ["ceo", "cfo", "cto", "cmo"]
        registry.get.side_effect = make_agent
        return registry

    def test_analysis_does_no_work_when_cancelled_upfront(self):
        calls = []
        event = threading.Event()
        event.set()
        orch = Orchestrator(self._registry(calls))
        orch.initialize(self._state(event))

        orch.run_analysis()

        assert calls == []

    def test_analysis_stops_after_the_agent_that_triggers_cancellation(self):
        calls = []
        event = threading.Event()
        registry = Mock()
        registry.list_names.return_value = ["ceo", "cfo", "cto", "cmo"]

        def make_agent(name):
            agent = Mock()

            def analyze(state, n=name):
                calls.append(n)
                event.set()  # user hits stop during the first real agent
                return Mock(
                    title="t", summary="s", key_findings=[], recommendations=[], risks=[],
                    alignment_score=0.8, get_role_specific_fields=lambda: {},
                )

            agent.analyze.side_effect = analyze
            return agent

        registry.get.side_effect = make_agent
        orch = Orchestrator(registry)
        orch.initialize(self._state(event))

        orch.run_analysis()

        # One agent ran; the rest were skipped rather than the whole phase lost.
        assert len(calls) == 1

    def test_run_skips_deliberation_but_still_synthesizes(self):
        event = threading.Event()
        event.set()
        orch = Orchestrator(self._registry([]))
        orch.initialize(self._state(event))
        orch.state.agent_outputs = {"cfo": Mock()}

        with patch.object(orch, 'run_inception'), \
             patch.object(orch, 'run_analysis'), \
             patch.object(orch, 'run_deliberation') as deliberation, \
             patch.object(orch, 'run_synthesis', return_value={"ok": True}) as synthesis:
            result = orch.run()

        deliberation.assert_not_called()
        synthesis.assert_called_once()
        assert result == {"ok": True}

    def test_run_returns_empty_when_cancelled_before_any_report(self):
        """run_synthesis raises on empty agent_outputs; that must not surface
        as a bogus failure for a run the user deliberately stopped."""
        event = threading.Event()
        event.set()
        orch = Orchestrator(self._registry([]))
        orch.initialize(self._state(event))

        with patch.object(orch, 'run_inception'), \
             patch.object(orch, 'run_analysis'), \
             patch.object(orch, 'run_synthesis') as synthesis:
            result = orch.run()

        assert result == {}
        synthesis.assert_not_called()

    def test_state_without_cancel_event_runs_every_phase(self):
        """CLI regression guard: no attached event means no behavior change."""
        orch = Orchestrator(self._registry([]))
        orch.initialize(self._state())
        orch.teams_enabled = True

        with patch.object(orch, 'run_inception') as inception, \
             patch.object(orch, 'run_analysis') as analysis, \
             patch.object(orch, 'run_team_deliberation') as teams, \
             patch.object(orch, 'run_deliberation') as deliberation, \
             patch.object(orch, 'run_synthesis', return_value={}):
            orch.run()

        for phase in (inception, analysis, teams, deliberation):
            phase.assert_called_once()


class TestAgentSpeakingEmission:
    """agent_speaking drives the "thinking" indicator, so it must fire before
    the LLM call, not after it."""

    def test_speaking_precedes_each_analysis_report(self):
        from openexec.events import EventType

        state = SimulationState(core_prompt="Should we expand?")
        state.active_agents = ["ceo", "cfo", "cto", "cmo"]

        registry = Mock()
        registry.list_names.return_value = ["ceo", "cfo", "cto", "cmo"]
        registry.get.side_effect = lambda name: Mock(
            analyze=Mock(return_value=Mock(
                title="t", summary="s", key_findings=[], recommendations=[],
                risks=[], alignment_score=0.8,
            ))
        )

        orch = Orchestrator(registry)
        orch.initialize(state)
        emitted = []
        sink = Mock()
        sink.append.side_effect = lambda e: emitted.append(e)
        orch.set_event_store(sink)

        orch.run_analysis()

        pairs = [
            e for e in emitted
            if e.event_type in (EventType.AGENT_SPEAKING, EventType.AGENT_REPORT_GENERATED)
        ]
        # CEO is skipped in analysis, so three agents report.
        assert len(pairs) == 6
        for speaking, report in zip(pairs[::2], pairs[1::2]):
            assert speaking.event_type == EventType.AGENT_SPEAKING
            assert report.event_type == EventType.AGENT_REPORT_GENERATED
            assert speaking.agent_name == report.agent_name
