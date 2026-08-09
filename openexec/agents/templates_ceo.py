from typing import TYPE_CHECKING

from .templates_base import AgentTemplate

if TYPE_CHECKING:
    pass


class CEOTemplate(AgentTemplate):
    """CEO implementation focusing on Vision and Strategy (Why?)."""

    name = "ceo"
    role = "Chief Executive Officer"
    focus = "Why?"
    analyze_msg = "CEO Analyzing: Defining the overarching strategic direction..."
    fallback_title = "CEO Strategic Vision Report"
    fallback_alignment = 0.75
    fallback_focus_areas = ["Vision", "Alignment"]
    fallback_recommendations = [
        "Prioritize alignment between the financial constraints (CFO) and the technological feasibility (CTO).",
        "Focus initial strategy on the market fit identified by the CMO data."
    ]
    fallback_risks = [
        "Risk of strategic misalignment if technical debt is ignored.",
        "Risk of poor market adoption if marketing strategy is disconnected from product reality."
    ]
    _SYNTHESIZE_MODALITY = "Ensure the final output reflects the team's research."

    def _fallback_summary(self, state) -> str:
        return f"The core problem is {state.core_prompt}. The goal is to determine the optimal path forward given the provided Data Corpus."

    def _fallback_findings(self, state) -> list[str]:
        findings = [f"Core conflict: {state.core_prompt}"]
        if state.data_corpus:
            for filename, content in state.data_corpus.items():
                findings.append(f"Data from '{filename}' suggests: {content[:100]}...")
        return findings