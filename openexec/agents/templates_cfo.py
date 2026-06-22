from .interface import AgentReport
from typing import Any


class CFOTemplate:
    """Concrete CFO implementation focusing on Financial Modeling and ROI (How much?)."""

    name = "cfo"
    role = "Chief Financial Officer"
    focus = "How much?"

    def __init__(self):
        """Initialize CFO agent with AI client."""
        try:
            from openexec.ai import AIClient, get_agent_system_prompt, build_analysis_prompt
            self.ai_client = AIClient()
            self.system_prompt = get_agent_system_prompt("cfo")
            self.use_ai = True
        except Exception as e:
            print(f"Warning: AI client initialization failed: {e}")
            print("Falling back to hardcoded analysis.")
            self.use_ai = False

    def analyze(self, state: 'SimulationState') -> AgentReport:
        """CFO analysis - financial modeling, risk/reward, ROI, budget constraints."""
        print("CFO Analyzing: Conducting financial modeling and ROI assessment...")

        if self.use_ai:
            try:
                from openexec.ai import build_analysis_prompt

                prompt = build_analysis_prompt(
                    core_prompt=state.core_prompt,
                    data_corpus=state.data_corpus,
                    agent_name="cfo",
                    assumptions=state.assumptions if hasattr(state, 'assumptions') else None
                )

                response_data = self.ai_client.complete_json_with_retry(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    temperature=0.7
                )

                return AgentReport.from_llm_response("cfo", response_data)
            except Exception as e:
                print(f"AI analysis failed: {e}")
                print("Falling back to hardcoded analysis.")
                # Fall through to hardcoded analysis

        # Hardcoded fallback analysis
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
            alignment_score=0.65,
            reasoning={
                "data_used": list(state.data_corpus.keys()),
                "focus_areas": ["Budget", "ROI"]
            }
        )
        return report

    def synthesize_team_position(self, team_reports: Dict[str, AgentReport], state: 'SimulationState') -> AgentReport:
        """Synthesize reports from the CFO's team into a consolidated financial position."""
        print("CFO Synthesizing: Consolidating input from Financial Analyst, Budget Planner, and Risk Analyst...")

        team_context = "\n\n## INTERNAL TEAM REPORTS\n"
        for member_name, report in team_reports.items():
            team_context += f"\n### {member_name.upper()} Report\n- Summary: {report.summary}\n- Findings: {report.key_findings}\n"

        enhanced_prompt = f"{state.core_prompt}\n\n{team_context}\n\n" \
                         "Review the reports from your specialized financial team. Synthesize their findings " \
                         "into a single, cohesive financial position for the board."

        system_prompt = self.system_prompt + "\n\nMODALITY: You are now synthesizing team input. " \
                                           "Ensure the final output reflects the team's quantitative research."

        try:
            response_data = self.ai_client.complete_json_with_retry(
                prompt=enhanced_prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            return AgentReport.from_llm_response("cfo", response_data)
        except Exception as e:
            print(f"CFO Synthesis failed: {e}. Falling back to standard analysis.")
            return self.analyze(state)


    def review_others(self, reports: dict[str, AgentReport]) -> None:
        """Delegation handled by DeliberationOrchestrator. See Orchestrator.run_review()."""
        pass
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
