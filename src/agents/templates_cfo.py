from .interface import AgentReport
from typing import Any


class CFOTemplate:
    """Concrete CFO implementation focusing on Financial Modeling and ROI (How much?)."""

    name = "cfo"
    role = "Chief Financial Officer"
    focus = "How much?"

    def analyze(self, state: 'SimulationState') -> AgentReport:
        """CFO analysis - financial modeling, risk/reward, ROI, budget constraints."""
        print("CFO Analyzing: Conducting financial modeling and ROI assessment...")

        # In a real implementation, this would involve deep financial calculations.
        summary = f"The potential opportunity is {state.core_prompt}. Financial viability depends on aligning projected costs with the Data Corpus."
        key_findings = [f"Financial viability hinges on cost projections from data sources."]

        if state.data_corpus:
            for filename, content in state.data_corpus.items():
                key_findings.append(f"Data from '{filename}' provides input for ROI calculation.")

        recommendations = [
            "Establish a clear budget baseline derived from the Data Corpus.",
            "Perform sensitivity analysis on cost projections to determine risk exposure."
        ]
        risks = [
            "Risk of over-budgeting if technical implementation costs are underestimated (CTO's view).",
            "Risk of underestimating market penetration potential (CMO's view)."
        ]

        report = AgentReport(
            title="CFO Financial Viability Report",
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks,
            confidence_score=0.65, # Moderate confidence, requires cross-referencing
            reasoning={
                "data_used": list(state.data_corpus.keys()),
                "focus_areas": ["Budget", "ROI"]
            }
        )
        return report


    def review_others(self, reports: dict[str, AgentReport]) -> None:
        """CFO reviews other agents for financial feasibility."""
        print("CFO Reviewing: Checking technical and market risks against budget.")

        # Check CTO's feasibility and CMO's market risk against financial constraints.
        cto_report = reports.get("cto")
        cmo_report = reports.get("cmo")

        if cto_report and cmo_report:
            technical_risk = cto_report.risks
            market_risk = cmo_report.risks

            print(f"Risk Cross-check: Financial vs. Technical risk assessment")
            if technical_risk and market_risk:
                print("High Risk Detected: Financial and Technical projections need alignment.")

        # The CFO synthesizes these into a unified risk assessment for the board.