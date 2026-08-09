from typing import TYPE_CHECKING

from .templates_base import AgentTemplate

if TYPE_CHECKING:
    pass


class CMOTemplate(AgentTemplate):
    """CMO implementation focusing on Market Positioning and GTM (Who to win?)."""

    name = "cmo"
    role = "Chief Marketing Officer"
    focus = "Who to win?"
    analyze_msg = "CMO Analyzing: Evaluating market positioning and GTM strategy..."
    fallback_title = "CMO Go-to-Market Strategy Report"
    fallback_alignment = 0.7
    fallback_focus_areas = ["Marketing", "Customer Fit"]
    fallback_recommendations = [
        "Launch with a focused Minimum Viable Product (MVP) targeting the most receptive segment.",
        "Develop a marketing narrative that explicitly addresses the technical and financial implications."
    ]
    fallback_risks = [
        "Risk of feature creep based on internal enthusiasm rather than market pull.",
        "Risk of misallocating marketing spend based on flawed customer perception data."
    ]
    _SYNTHESIZE_MODALITY = "Ensure the final output reflects the team's market research."

    def _fallback_summary(self, state) -> str:
        return f"The market for {state.core_prompt} is defined by current trends and potential customer segments in the Data Corpus."

    def _fallback_findings(self, state) -> list[str]:
        findings: list[str] = []
        if state.data_corpus:
            findings.append(f"Target segment analysis from '{list(state.data_corpus.keys())[0]}' indicates high potential interest.")
            for filename, content in state.data_corpus.items():
                findings.append(f"Market reception insight from '{filename}': {content[:100]}...")
        else:
            findings.append("No specific market data provided; analysis based on general market principles.")
        return findings