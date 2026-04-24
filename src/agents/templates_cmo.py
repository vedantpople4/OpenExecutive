from .interface import AgentReport
from typing import Any


class CNOTemplate:
    """Concrete CMO implementation focusing on Market Reception and Go-to-Market (How to sell it?)."""

    name = "cmo"
    role = "Chief Marketing Officer"
    focus = "How to sell it?"

    def analyze(self, state: 'SimulationState') -> AgentReport:
        """CMO analysis - market reception, go-to-market, customer fit."""
        print("CMO Analyzing: Assessing market reception and go-to-market strategy...")

        # In a real implementation, this would involve persona modeling based on the data corpus.
        summary = f"The market for {state.core_prompt} is defined by current trends and potential customer segments in the Data Corpus."
        key_findings = []

        if state.data_corpus:
            key_findings.append(f"Target segment analysis from '{list(state.data_corpus.keys())[0]}' indicates high potential interest.")
            for filename, content in state.data_corpus.items():
                key_findings.append(f"Market reception insight from '{filename}': {content[:100]}...")
        else:
            key_findings.append("No specific market data provided; analysis based on general market principles.")

        recommendations = [
            "Launch with a focused Minimum Viable Product (MVP) targeting the most receptive segment.",
            "Develop a marketing narrative that explicitly addresses the technical and financial implications."
        ]
        risks = [
            "Risk of feature creep based on internal enthusiasm rather than market pull.",
            "Risk of misallocating marketing spend based on flawed customer perception data."
        ]

        report = AgentReport(
            title="CMO Go-to-Market Strategy Report",
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks,
            confidence_score=0.7, # High confidence in market framing
            reasoning={
                "data_used": list(state.data_corpus.keys()),
                "focus_areas": ["Marketing", "Customer Fit"]
            }
        )
        return report


    def review_others(self, reports: dict[str, AgentReport]) -> None:
        """CMO reviews other agents for market alignment."""
        print("CMO Reviewing: Checking technical and financial constraints against market goals.")

        # Check CTO's feasibility and CFO's budget against the marketing strategy.
        cto_report = reports.get("cto")
        cfo_report = reports.get("cfo")

        if cto_report and cfo_report:
            print(f"Alignment Check: Marketing focus must respect technical feasibility ({cto_report.recommendations[0]}) and budget constraints ({cfo_report.recommendations[0]}).")
            # Placeholder for deeper conflict resolution logic
        else:
             print("Warning: Missing technical or financial reports; market strategy lacks necessary context.")

        # The CMO ensures the proposed plan is commercially executable.