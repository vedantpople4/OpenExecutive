from openexec.agents.interface import AgentReport
from openexec.event_store import EventStore
from openexec.events import (
    Event, EventType, SimulationInitialized, InceptionStarted,
    InceptionCompleted, AnalysisStarted, AgentReportGenerated,
    AnalysisCompleted, DeliberationStarted, DeliberationRoundStarted,
    DeliberationRoundCompleted, DeliberationCompleted, SynthesisStarted,
    SynthesisCompleted, ErrorOccurred
)
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass
class SimulationState:
    """Current state of a simulation run."""

    simulation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    core_prompt: str = ""
    data_corpus: Dict[str, str] = field(default_factory=dict)
    decision_point: str | None = None
    status: str = "idle"
    phase: str = ""
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    deliberation_round: int = 0
    challenges: Dict[str, list[str]] = field(default_factory=dict)
    deliberation_outputs: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    board_summary: str = ""
    assumptions: Dict[str, str] = field(default_factory=dict)
    agent_weights: Dict[str, float] = field(default_factory=dict)  # agent_name -> weight (0.0-1.0)  # assumption_key -> assumption_value


class BaseOrchestrator(ABC):
    """Abstract base for simulation orchestrators."""

    @abstractmethod
    def initialize(self, state: SimulationState) -> None:
        """Initialize the simulation with briefing data."""
        pass

    @abstractmethod
    def run_inception(self) -> None:
        """Run Phase 1: Inception - receive prompt and delegate tasks."""
        pass

    @abstractmethod
    def run_analysis(self) -> None:
        """Run Phase 2: Individual Research - collect expert reports."""
        pass

    @abstractmethod
    def run_review(self) -> None:
        """Run Phase 3: Cross-Functional Review - manage feedback loops."""
        pass

    @abstractmethod
    def run_synthesis(self) -> Dict[str, Any]:
        """Run Phase 4: Synthesis - draft final document."""
        pass


class Orchestrator(BaseOrchestrator):
    """Manages the multi-agent simulation workflow with Event Sourcing."""

    def __init__(self, registry):
        self.registry = registry
        self.state: SimulationState | None = None
        self.event_store: EventStore | None = None

    def set_event_store(self, event_store: EventStore) -> None:
        """Set the event store for this orchestrator.

        Args:
            event_store: The EventStore instance to use for event emission
        """
        self.event_store = event_store

    def _emit_event(self, event: Event) -> None:
        """Emit an event to the event store if one is configured.

        Args:
            event: The event to emit
        """
        if self.event_store and self.state:
            event.aggregate_id = self.state.simulation_id
            self.event_store.append(event)

    def initialize(self, state: SimulationState) -> None:
        """Initialize the simulation with briefing data."""
        self.state = state

        agent_names = list(self.registry.list_names())

        self._emit_event(SimulationInitialized(
            event_id=str(uuid.uuid4()),
            aggregate_id=state.simulation_id,
            core_prompt=state.core_prompt,
            decision_point=state.decision_point,
            agent_names=agent_names
        ))

        print("Orchestrator Initialized.")
        print(f"Simulation Goal: {state.core_prompt}")
        print(f"Decision Point: {state.decision_point}")
        print("-" * 40)

    def run_inception(self) -> None:
        """Phase 1: Inception - Receive prompt and delegate tasks."""
        if not self.state:
            raise ValueError("Simulation not initialized.")

        self._emit_event(InceptionStarted(
            event_id=str(uuid.uuid4()),
            aggregate_id=self.state.simulation_id
        ))

        print("\n--- Phase 1: INCEPTION ---")

        self._delegate_task(
            "ceo",
            state=self.state,
            phase="inception"
        )

        ceo_report_dict = None
        if "ceo" in self.state.agent_outputs:
            report = self.state.agent_outputs["ceo"]
            if hasattr(report, 'title'):
                ceo_report_dict = {
                    "title": report.title,
                    "summary": report.summary,
                    "key_findings": report.key_findings,
                    "recommendations": report.recommendations,
                    "risks": report.risks,
                    "alignment_score": report.alignment_score,
                }

        self._emit_event(InceptionCompleted(
            event_id=str(uuid.uuid4()),
            aggregate_id=self.state.simulation_id,
            ceo_report=ceo_report_dict
        ))

    def run_analysis(self) -> None:
        """Phase 2: Individual Research - Collect expert reports."""
        if not self.state:
            raise ValueError("Simulation not initialized.")

        self._emit_event(AnalysisStarted(
            event_id=str(uuid.uuid4()),
            aggregate_id=self.state.simulation_id
        ))

        print("\n--- Phase 2: ANALYSIS ---")
        agent_names = self.registry.list_names()
        reports: Dict[str, Any] = {}

        for name in agent_names:
            if name == "ceo":
                continue
            print(f"Delegating analysis to {name}...")
            agent = self.registry.get(name)
            if agent:
                report = agent.analyze(self.state)
                reports[name] = report

                self._emit_event(AgentReportGenerated(
                    event_id=str(uuid.uuid4()),
                    aggregate_id=self.state.simulation_id,
                    agent_name=name,
                    report_data={
                        "title": report.title,
                        "summary": report.summary,
                        "key_findings": report.key_findings,
                        "recommendations": report.recommendations,
                        "risks": report.risks,
                        "alignment_score": report.alignment_score,
                    }
                ))

        self.state.agent_outputs.update(reports)
        self._emit_event(AnalysisCompleted(
            event_id=str(uuid.uuid4()),
            aggregate_id=self.state.simulation_id,
            reports_generated=list(reports.keys())
        ))

        print("\n--- Analysis Complete. Reports Collected ---")

    def run_review(self) -> None:
        """Deprecated: deliberation now runs via run_deliberation(). Forwarding for compatibility."""
        self.run_deliberation()

    def run_deliberation(self) -> None:
        """Phase 3: Multi-round deliberation — board meeting workflow."""
        if not self.state or not self.registry.list_names():
            raise ValueError("Simulation not initialized or no agents registered.")

        from .orchestrator_deliberation import DeliberationOrchestrator

        self._emit_event(DeliberationStarted(
            event_id=str(uuid.uuid4()),
            aggregate_id=self.state.simulation_id
        ))

        print("\n--- Phase 3: DELIBERATION ---")
        delib = DeliberationOrchestrator(self.state, self.registry)

        for round_num in range(1, 6):
            self._emit_event(DeliberationRoundStarted(
                event_id=str(uuid.uuid4()),
                aggregate_id=self.state.simulation_id,
                round_number=round_num
            ))

        delib.run_deliberation()

        for round_num, round_reports in self.state.deliberation_outputs.items():
            self._emit_event(DeliberationRoundCompleted(
                event_id=str(uuid.uuid4()),
                aggregate_id=self.state.simulation_id,
                round_number=round_num,
                reports={
                    name: {
                        "title": r.title,
                        "summary": r.summary,
                        "key_findings": r.key_findings,
                        "recommendations": r.recommendations,
                        "risks": r.risks,
                    }
                    for name, r in round_reports.items() if isinstance(r, AgentReport)
                }
            ))

        self._emit_event(DeliberationCompleted(
            event_id=str(uuid.uuid4()),
            aggregate_id=self.state.simulation_id,
            total_rounds=5
        ))

        print("\n--- Deliberation Rounds Complete ---")

    def run_synthesis(self) -> Dict[str, Any]:
        """Phase 4: Synthesis - Draft the final document."""
        if not self.state or not self.state.agent_outputs:
            raise ValueError("Simulation is incomplete. Cannot synthesize without agent reports.")

        self._emit_event(SynthesisStarted(
            event_id=str(uuid.uuid4()),
            aggregate_id=self.state.simulation_id
        ))

        print("\n--- Phase 4: SYNTHESIS ---")

        # Build executive summary from CEO synthesis if available
        ceo_r5 = self.state.deliberation_outputs.get(5, {}).get("ceo")
        board_summary = None
        if ceo_r5 and hasattr(ceo_r5, "board_decision") and ceo_r5.board_decision:
            board_summary = ceo_r5.board_decision.get("summary", "")
        elif ceo_r5 and isinstance(ceo_r5, dict):
            bd = ceo_r5.get("board_decision", {})
            if isinstance(bd, dict):
                board_summary = bd.get("summary", "")
        executive_summary = board_summary or self.state.core_prompt

        final_report: Dict[str, Any] = {
            "simulation_id": self.state.simulation_id,
            "executive_summary": executive_summary,
            "decision_point": self.state.decision_point,
            "agent_reports": {},
            "data_sources": {
                "sources_accessed": [],
                "sources_failed": [],
                "all_available_sources": [],
                "access_success_rate": 0.0,
                "timestamp": ""
            }
        }

        all_sources_accessed = set()
        all_sources_failed = set()
        all_available_sources = set()
        data_timestamps = []

        for name, report in self.state.agent_outputs.items():
            print(f"Synthesizing {name}'s view...")
            report_dict: Dict[str, Any] = {
                "title": report.title,
                "summary": report.summary,
                "key_findings": report.key_findings,
                "recommendations": report.recommendations,
                "risks": report.risks,
                "alignment_score": report.alignment_score,
            }
            role_specific = report.get_role_specific_fields()
            if role_specific:
                report_dict.update(role_specific)
            # NOTE: Keep individual agent reports as Phase-2 (analysis) outputs.
            # Deliberation outputs live in `deliberation_rounds` for transcript.
            final_report["agent_reports"][name] = report_dict

            if (hasattr(report, 'reasoning')
                    and isinstance(report.reasoning, dict)
                    and report.reasoning
                    and report.reasoning.get('real_time_data_used')):
                if 'sources_accessed' in report.reasoning:
                    all_sources_accessed.update(report.reasoning['sources_accessed'])
                if 'sources_failed' in report.reasoning:
                    all_sources_failed.update(report.reasoning['sources_failed'])
                if 'all_available_sources' in report.reasoning:
                    all_available_sources.update(report.reasoning['all_available_sources'])
                if 'data_timestamp' in report.reasoning:
                    data_timestamps.append(report.reasoning['data_timestamp'])

        # Track data corpus sources (loaded from data/ directory in main.py)
        if self.state.data_corpus:
            for filename in self.state.data_corpus.keys():
                all_available_sources.add(filename)
                all_sources_accessed.add(filename)

        ceo_r5 = self.state.deliberation_outputs.get(5, {}).get("ceo")
        if ceo_r5 and hasattr(ceo_r5, "board_decision") and ceo_r5.board_decision:
            final_report["board_decision"] = ceo_r5.board_decision

        if self.state.deliberation_outputs:
            final_report["deliberation_rounds"] = {}
            for rnd, outputs in self.state.deliberation_outputs.items():
                if rnd == 0:
                    continue
                final_report["deliberation_rounds"][rnd] = {
                    name: self._report_to_dict(report)
                    for name, report in outputs.items()
                    if isinstance(report, AgentReport)
                }

        final_report["synthesized_recommendations"] = self._synthesize_recommendations()
        final_report["overall_risk_assessment"] = self._synthesize_risks()

        final_report["data_sources"] = {
            "sources_accessed": list(all_sources_accessed),
            "sources_failed": list(all_sources_failed),
            "all_available_sources": list(all_available_sources),
            "access_success_rate": self._calculate_success_rate(all_sources_accessed, all_sources_failed),
            "timestamp": data_timestamps[0] if data_timestamps else "Unknown"
        }

        self._emit_event(SynthesisCompleted(
            event_id=str(uuid.uuid4()),
            aggregate_id=self.state.simulation_id,
            final_report=final_report
        ))

        return final_report

    def _report_to_dict(self, report: AgentReport) -> Dict[str, Any]:
        """Convert an AgentReport to a JSON-serialisable dict."""
        return {
            "title": report.title,
            "summary": report.summary,
            "key_findings": report.key_findings,
            "recommendations": report.recommendations,
            "risks": report.risks,
            "alignment_score": report.alignment_score,
            "round_number": report.round_number,
            ** report.get_role_specific_fields(),
        }

    def _calculate_success_rate(self, accessed: set, failed: set) -> float:
        """Calculate data access success rate."""
        total = len(accessed) + len(failed)
        if total == 0:
            return 0.0
        return len(accessed) / total

    def _synthesize_recommendations(self) -> list[str]:
        """Synthesize recommendations from all agents.
        
        When agent_weights are set, recommendations from higher-weighted agents
        are tagged with priority indicators.
        """
        recommendations = []
        weights = self.state.agent_weights if hasattr(self.state, 'agent_weights') else {}
        
        for name, report in self.state.agent_outputs.items():
            if hasattr(report, 'recommendations'):
                weight = weights.get(name.lower(), 1.0)  # Default weight is 1.0 if not specified
                for rec in report.recommendations:
                    if weight < 1.0:
                        # Add weight indicator for non-default weights
                        recommendations.append(f"[{name.upper()}][W:{weight:.1f}] {rec}")
                    else:
                        recommendations.append(f"[{name.upper()}] {rec}")
        return recommendations

    def _synthesize_risks(self) -> list[str]:
        """Synthesize risks from all agents.
        
        When agent_weights are set, risks from higher-weighted agents
        are tagged with priority indicators.
        """
        risks = []
        weights = self.state.agent_weights if hasattr(self.state, 'agent_weights') else {}
        
        for name, report in self.state.agent_outputs.items():
            if hasattr(report, 'risks'):
                weight = weights.get(name.lower(), 1.0)
                for risk in report.risks:
                    if weight < 1.0:
                        risks.append(f"[{name.upper()}][W:{weight:.1f}] {risk}")
                    else:
                        risks.append(f"[{name.upper()}] {risk}")
        return risks

    def _delegate_task(self, agent_name: str, state: SimulationState, phase: str) -> None:
        """Helper to delegate a task."""
        agent = self.registry.get(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found in registry.")

        if phase == "inception":
            report = agent.analyze(state)
            self.state.agent_outputs[agent_name] = report
        elif phase == "analysis":
            report = agent.analyze(state)
            self.state.agent_outputs[agent_name] = report
        elif phase == "review":
            agent.review_others(self.state.agent_outputs)

    def run(self) -> Dict[str, Any]:
        """Executes the full simulation workflow."""
        if not self.state:
            raise ValueError("Orchestrator must be initialized before running.")

        print("\n===========================================")
        print("STARTING FULL EXECUTIVE BOARD SIMULATION")
        print("===========================================")

        try:
            self.run_inception()
            self.run_analysis()
            self.run_review()
            final_results = self.run_synthesis()

            print("\n===========================================")
            print("SIMULATION COMPLETE")
            print("===========================================")

            return final_results
        except Exception as e:
            self._emit_event(ErrorOccurred(
                event_id=str(uuid.uuid4()),
                aggregate_id=self.state.simulation_id if self.state else "",
                error_message=str(e),
                phase=self.state.phase if self.state else "unknown"
            ))
            raise
