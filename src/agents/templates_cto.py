from .interface import AgentReport
from typing import Any


class CTOTemplate:
    """Concrete CTO implementation focusing on Technical Feasibility and Scalability (How to build it?)."""

    name = "cto"
    role = "Chief Technology Officer"
    focus = "How to build it?"

    def __init__(self):
        """Initialize CTO agent with AI client."""
        try:
            from src.ai import AIClient, get_agent_system_prompt, build_analysis_prompt
            self.ai_client = AIClient()
            self.system_prompt = get_agent_system_prompt("cto")
            self.use_ai = True
        except Exception as e:
            print(f"Warning: AI client initialization failed: {e}")
            print("Falling back to hardcoded analysis.")
            self.use_ai = False

    def analyze(self, state: 'SimulationState') -> AgentReport:
        """CTO analysis - technical feasibility, scalability, architecture."""
        print("CTO Analyzing: Assessing architectural feasibility and scalability...")

        if self.use_ai:
            try:
                from src.ai import build_analysis_prompt

                # Build AI prompt
                prompt = build_analysis_prompt(
                    core_prompt=state.core_prompt,
                    data_corpus=state.data_corpus,
                    agent_name="cto"
                )

                # Call LLM
                response_data = self.ai_client.complete_json(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    temperature=0.7
                )

                # Parse response into AgentReport
                return AgentReport(
                    title=response_data.get("title", "CTO Technical Feasibility Report"),
                    summary=response_data.get("summary", ""),
                    key_findings=response_data.get("key_findings", []),
                    recommendations=response_data.get("recommendations", []),
                    risks=response_data.get("risks", []),
                    confidence_score=float(response_data.get("confidence_score", 0.8)),
                    reasoning=response_data.get("reasoning", {})
                )
            except Exception as e:
                print(f"AI analysis failed: {e}")
                print("Falling back to hardcoded analysis.")
                # Fall through to hardcoded analysis

        # Hardcoded fallback analysis
        summary = f"The proposed solution for {state.core_prompt} requires assessing the current system's capacity against projected growth."
        key_findings = [f"Current architecture shows potential bottlenecks related to scaling."]

        if state.data_corpus:
            for filename, content in state.data_corpus.items():
                key_findings.append(f"Data from '{filename}' highlights scalability concerns regarding {content[:100]}...")

        recommendations = [
            "Implement a microservices architecture to decouple scaling bottlenecks.",
            "Mandate end-to-end testing across all proposed data flows before deployment."
        ]
        risks = [
            "Risk of technical debt accumulating if expediency is prioritized over scalable design.",
            "Risk of system failure under peak load due to inadequate infrastructure planning."
        ]

        report = AgentReport(
            title="CTO Technical Feasibility Report",
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks,
            confidence_score=0.8,
            reasoning={
                "data_used": list(state.data_corpus.keys()),
                "focus_areas": ["Architecture", "Scalability"]
            }
        )
        return report


    def review_others(self, reports: dict[str, AgentReport]) -> None:
        """CTO reviews other agents for technical alignment."""
        print("CTO Reviewing: Checking financial and market implications of technical choices.")

        # Cross-check with CFO's budget concerns and CMO's market needs.
        cfo_report = reports.get("cfo")
        cmo_report = reports.get("cmo")

        if cfo_report and cmo_report:
            print(f"Alignment Check: Technical recommendations must be cost-effective ({cfo_report.recommendations[0]}) and market-validated ({cmo_report.recommendations[0]}).")
            # Placeholder for deeper conflict resolution logic
        else:
             print("Warning: Missing financial or market reports; technical recommendations lack full context.")

        # The CTO ensures the proposed technical path is both feasible and commercially viable.
