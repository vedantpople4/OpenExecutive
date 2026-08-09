from typing import TYPE_CHECKING

from .templates_base import AgentTemplate

if TYPE_CHECKING:
    pass


class CTOTemplate(AgentTemplate):
    """CTO implementation focusing on Technical Feasibility and Scalability (How to build it?)."""

    name = "cto"
    role = "Chief Technology Officer"
    focus = "How to build it?"
    analyze_msg = "CTO Analyzing: Assessing architectural feasibility and scalability..."
    fallback_title = "CTO Technical Feasibility Report"
    fallback_alignment = 0.8
    fallback_focus_areas = ["Architecture", "Scalability"]
    fallback_recommendations = [
        "Implement a microservices architecture to decouple scaling bottlenecks.",
        "Mandate end-to-end testing across all proposed data flows before deployment."
    ]
    fallback_risks = [
        "Risk of technical debt accumulating if expediency is prioritized over scalable design.",
        "Risk of system failure under peak load due to inadequate infrastructure planning."
    ]
    _SYNTHESIZE_MODALITY = "Ensure the final output reflects the team's technical research."

    def _fallback_summary(self, state) -> str:
        return f"The proposed solution for {state.core_prompt} requires assessing the current system's capacity against projected growth."

    def _fallback_findings(self, state) -> list[str]:
        findings = ["Current architecture shows potential bottlenecks related to scaling."]
        if state.data_corpus:
            for filename, content in state.data_corpus.items():
                findings.append(f"Data from '{filename}' highlights scalability concerns regarding {content[:100]}...")
        return findings