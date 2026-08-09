from typing import TYPE_CHECKING

from .templates_base import AgentTemplate

if TYPE_CHECKING:
    pass


class CFOTemplate(AgentTemplate):
    """CFO implementation focusing on Financial Modeling and ROI (How much?)."""

    name = "cfo"
    role = "Chief Financial Officer"
    focus = "How much?"
    analyze_msg = "CFO Analyzing: Conducting financial modeling and ROI assessment..."
    fallback_title = "CFO Financial Viability Report"
    fallback_alignment = 0.65
    fallback_focus_areas = ["Budget", "ROI"]
    fallback_recommendations = [
        "Establish a clear budget baseline derived from the Data Corpus.",
        "Perform sensitivity analysis on cost projections to determine risk exposure."
    ]
    fallback_risks = [
        "Risk of over-budgeting if technical implementation costs are underestimated (CTO's view).",
        "Risk of underestimating market penetration potential (CMO's view)."
    ]
    _SYNTHESIZE_MODALITY = "Ensure the final output reflects the team's quantitative research."

    def _fallback_summary(self, state) -> str:
        return f"The potential opportunity is {state.core_prompt}. Financial viability depends on aligning projected costs with the Data Corpus."

    def _fallback_findings(self, state) -> list[str]:
        findings = ["Financial viability hinges on cost projections from data sources."]
        if state.data_corpus:
            for filename, _content in state.data_corpus.items():
                findings.append(f"Data from '{filename}' provides input for ROI calculation.")
        return findings