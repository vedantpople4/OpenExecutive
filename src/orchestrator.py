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
        """Phase 3: Cross-Functional Review - Manage feedback loops."""
        if not self.state or not self.registry.list_names():
            raise ValueError("Simulation not initialized or no agents registered.")

        print("\n--- Phase 3: CROSS-FUNCTIONAL REVIEW ---")

        # Run the review step based on agent templates
        for name in self.registry.list_names():
            agent = self.registry.get(name)
            if agent and hasattr(agent, 'review_others'):
                print(f"Agent {name} reviewing others...")
                agent.review_others(self.state.agent_outputs)

        print("\n--- Review Complete. Cross-functional feedback integrated ---")

    def run_synthesis(self) -> Dict[str, Any]:
        """Phase 4: Synthesis - Draft the final document."""
        if not self.state or not self.state.agent_outputs:
            raise ValueError("Simulation is incomplete. Cannot synthesize without agent reports.")

        print("\n--- Phase 4: SYNTHESIS ---")

        # Synthesize all reports into a final document
        final_report = {
            "executive_summary": f"Executive Board Analysis for: {self.state.core_prompt}",
            "decision_point": self.state.decision_point,
            "agent_reports": {}
        }

        for name, report in self.state.agent_outputs.items():
            print(f"Synthesizing {name}'s view...")
            final_report["agent_reports"][name] = {
                "title": report.title,
                "summary": report.summary,
                "key_findings": report.key_findings,
                "recommendations": report.recommendations,
                "risks": report.risks,
                "confidence_score": report.confidence_score
            }

        # Add synthesized recommendations
        final_report["synthesized_recommendations"] = self._synthesize_recommendations()
        final_report["overall_risk_assessment"] = self._synthesize_risks()

        return final_report

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
