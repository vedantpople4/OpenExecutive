from src.agents.interface import AgentReport
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class SimulationState:
    """Current state of a simulation run."""

    core_prompt: str
    data_corpus: Dict[str, str] = field(default_factory=dict)  # filename -> content
    decision_point: str | None = None
    status: str = "idle"  # idle, analyzing, synthesizing, complete
    phase: str = ""
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    # Deliberation state
    deliberation_round: int = 0
    challenges: Dict[str, list[str]] = field(default_factory=dict)  # agent_name -> questions
    deliberation_outputs: Dict[int, Dict[str, Any]] = field(default_factory=dict)


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
    """Manages the multi-agent simulation workflow."""

    def __init__(self, registry):
        self.registry = registry
        self.state: SimulationState | None = None

    def initialize(self, state: SimulationState) -> None:
        """Initialize the simulation with briefing data."""
        self.state = state
        print("Orchestrator Initialized.")
        print(f"Simulation Goal: {state.core_prompt}")
        print(f"Decision Point: {state.decision_point}")
        print("-" * 40)

    def run_inception(self) -> None:
        """Phase 1: Inception - Receive prompt and delegate tasks."""
        if not self.state:
            raise ValueError("Simulation not initialized.")

        print("\n--- Phase 1: INCEPTION ---")
        # Delegate initial framing to the CEO for vision setting
        self._delegate_task(
            "ceo",
            state=self.state,
            phase="inception"
        )

    def run_analysis(self) -> None:
        """Phase 2: Individual Research - Collect expert reports."""
        if not self.state:
            raise ValueError("Simulation not initialized.")

        print("\n--- Phase 2: ANALYSIS ---")
        agent_names = self.registry.list_names()
        reports: Dict[str, Any] = {}

        # Delegate analysis tasks to relevant agents
        for name in agent_names:
            if name == "ceo":
                continue  # CEO already handled in inception
            print(f"Delegating analysis to {name}...")
            agent = self.registry.get(name)
            if agent:
                report = agent.analyze(self.state)
                reports[name] = report

        self.state.agent_outputs.update(reports)
        print("\n--- Analysis Complete. Reports Collected ---")

    def run_review(self) -> None:
        """Deprecated: deliberation now runs via run_deliberation(). Forwarding for compatibility."""
        self.run_deliberation()

    def run_deliberation(self) -> None:
        """Phase 3: Multi-round deliberation — board meeting workflow."""
        if not self.state or not self.registry.list_names():
            raise ValueError("Simulation not initialized or no agents registered.")

        from .orchestrator_deliberation import DeliberationOrchestrator

        print("\n--- Phase 3: DELIBERATION ---")
        delib = DeliberationOrchestrator(self.state, self.registry)
        delib.run_deliberation()
        print("\n--- Deliberation Rounds Complete ---")

    def run_synthesis(self) -> Dict[str, Any]:
        """Phase 4: Synthesis - Draft the final document."""
        if not self.state or not self.state.agent_outputs:
            raise ValueError("Simulation is incomplete. Cannot synthesize without agent reports.")

        print("\n--- Phase 4: SYNTHESIS ---")

        # Synthesize all reports into a final document
        final_report: Dict[str, Any] = {
            "executive_summary": f"Executive Board Analysis for: {self.state.core_prompt}",
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

        # Collect data sources from all agents
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
            # Add verdict based on agent role
            role_specific = report.get_role_specific_fields()
            if role_specific:
                report_dict.update(role_specific)
            # Prioritize final-round deliberation report over blind Phase-2 report
            delib_reports = self.state.deliberation_outputs.get(4, {}).get(name)
            if delib_reports and hasattr(delib_reports, "get_role_specific_fields"):
                delib_dict = self._report_to_dict(delib_reports)
                # Only override if the deliberation output has meaningful content
                if delib_dict.get("summary"):
                    report_dict.update(delib_dict)
            final_report["agent_reports"][name] = report_dict

            # Collect data sources from agent reasoning
            if (hasattr(report, 'reasoning')
                    and isinstance(report.reasoning, dict)
                    and report.reasoning
                    and report.reasoning.get('real_time_data_used')):
                    # Collect sources from reasoning
                    if 'sources_accessed' in report.reasoning:
                        all_sources_accessed.update(report.reasoning['sources_accessed'])
                    if 'sources_failed' in report.reasoning:
                        all_sources_failed.update(report.reasoning['sources_failed'])
                    if 'all_available_sources' in report.reasoning:
                        all_available_sources.update(report.reasoning['all_available_sources'])
                    if 'data_timestamp' in report.reasoning:
                        data_timestamps.append(report.reasoning['data_timestamp'])

        # Inject board decision from deliberation round 5 if available
        ceo_r5 = self.state.deliberation_outputs.get(5, {}).get("ceo")
        if ceo_r5 and hasattr(ceo_r5, "board_decision") and ceo_r5.board_decision:
            final_report["board_decision"] = ceo_r5.board_decision

        # Inject full deliberation transcript (all rounds visible)
        if self.state.deliberation_outputs:
            final_report["deliberation_rounds"] = {}
            for rnd, outputs in self.state.deliberation_outputs.items():
                if rnd == 0:
                    continue  # Skip blind Phase-2 reports — already in agent_reports
                final_report["deliberation_rounds"][rnd] = {
                    name: self._report_to_dict(report)
                    for name, report in outputs.items()
                    if isinstance(report, AgentReport)
                }

        # Add synthesized recommendations
        final_report["synthesized_recommendations"] = self._synthesize_recommendations()
        final_report["overall_risk_assessment"] = self._synthesize_risks()

        # Add data sources summary
        final_report["data_sources"] = {
            "sources_accessed": list(all_sources_accessed),
            "sources_failed": list(all_sources_failed),
            "all_available_sources": list(all_available_sources),
            "access_success_rate": self._calculate_success_rate(all_sources_accessed, all_sources_failed),
            "timestamp": data_timestamps[0] if data_timestamps else "Unknown"
        }

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
        """Calculate data access success rate.

        Args:
            accessed: Set of successfully accessed sources
            failed: Set of failed sources

        Returns:
            Success rate as percentage (0.0 to 1.0)
        """
        total = len(accessed) + len(failed)
        if total == 0:
            return 0.0
        return len(accessed) / total

    def _synthesize_recommendations(self) -> list[str]:
        """Synthesize recommendations from all agents."""
        recommendations = []
        for name, report in self.state.agent_outputs.items():
            if hasattr(report, 'recommendations'):
                recommendations.extend([f"[{name.upper()}] {rec}" for rec in report.recommendations])
        return recommendations

    def _synthesize_risks(self) -> list[str]:
        """Synthesize risks from all agents."""
        risks = []
        for name, report in self.state.agent_outputs.items():
            if hasattr(report, 'risks'):
                risks.extend([f"[{name.upper()}] {risk}" for risk in report.risks])
        return risks

    def _delegate_task(self, agent_name: str, state: SimulationState, phase: str) -> None:
        """Helper to delegate a task."""
        agent = self.registry.get(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found in registry.")

        if phase == "inception":
            # Special handling for inception (CEO sets the tone)
            report = agent.analyze(state)
            self.state.agent_outputs[agent_name] = report
        elif phase == "analysis":
            # Standard analysis delegation
            report = agent.analyze(state)
            self.state.agent_outputs[agent_name] = report
        elif phase == "review":
            # Review step
            agent.review_others(self.state.agent_outputs)

    def run(self) -> Dict[str, Any]:
        """Executes the full simulation workflow."""
        if not self.state:
            raise ValueError("Orchestrator must be initialized before running.")

        print("\n===========================================")
        print("STARTING FULL EXECUTIVE BOARD SIMULATION")
        print("===========================================")

        # 1. Inception
        self.run_inception()

        # 2. Analysis
        self.run_analysis()

        # 3. Review
        self.run_review()

        # 4. Synthesis
        final_results = self.run_synthesis()

        print("\n===========================================")
        print("SIMULATION COMPLETE")
        print("===========================================")

        return final_results
