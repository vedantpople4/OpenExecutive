from .interface import AgentReport
from typing import Any


class CMOTemplate:
    """Concrete CMO implementation focusing on Market Reception and Go-to-Market (How to sell it?)."""

    name = "cmo"
    role = "Chief Marketing Officer"
    focus = "How to sell it?"

    def __init__(self):
        """Initialize CMO agent with AI client."""
        try:
            from openexec.ai import AIClient, get_agent_system_prompt, build_analysis_prompt
            self.ai_client = AIClient()
            self.system_prompt = get_agent_system_prompt("cmo")
            self.use_ai = True
        except Exception as e:
            print(f"Warning: AI client initialization failed: {e}")
            print("Falling back to hardcoded analysis.")
            self.use_ai = False

    def analyze(self, state: 'SimulationState') -> AgentReport:
        """CMO analysis - market reception, go-to-market, customer fit."""
        print("CMO Analyzing: Assessing market reception and go-to-market strategy...")

        if self.use_ai:
            try:
                from openexec.ai import build_analysis_prompt

                prompt = build_analysis_prompt(
                    core_prompt=state.core_prompt,
                    data_corpus=state.data_corpus,
                    agent_name="cmo",
                    assumptions=state.assumptions if hasattr(state, 'assumptions') else None,
                    research_cfg=getattr(state, 'research_cfg', None),
                )

                response_data = self.ai_client.complete_json_with_retry(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    temperature=0.7
                )

                return AgentReport.from_llm_response("cmo", response_data)
            except Exception as e:
                print(f"AI analysis failed: {e}")
                print("Falling back to hardcoded analysis.")
                # Fall through to hardcoded analysis

        # Hardcoded fallback analysis
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
            alignment_score=0.7,
            reasoning={
                "data_used": list(state.data_corpus.keys()),
                "focus_areas": ["Marketing", "Customer Fit"]
            }
        )
        return report

    def synthesize_team_position(self, team_reports: Dict[str, AgentReport], state: 'SimulationState') -> AgentReport:
        """Synthesize reports from the CMO's team into a consolidated market position."""
        print("CMO Synthesizing: Consolidating input from Growth Marketer, Content Strategist, and SEO Specialist...")

        team_context = "\n\n## INTERNAL TEAM REPORTS\n"
        for member_name, report in team_reports.items():
            team_context += f"\n### {member_name.upper()} Report\n- Summary: {report.summary}\n- Findings: {report.key_findings}\n"

        enhanced_prompt = f"{state.core_prompt}\n\n{team_context}\n\n" \
                         "Review the reports from your specialized marketing team. Synthesize their findings " \
                         "into a single, cohesive market position for the board."

        system_prompt = self.system_prompt + "\n\nMODALITY: You are now synthesizing team input. " \
                                           "Ensure the final output reflects the team's market research."

        try:
            response_data = self.ai_client.complete_json_with_retry(
                prompt=enhanced_prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            return AgentReport.from_llm_response("cmo", response_data)
        except Exception as e:
            print(f"CMO Synthesis failed: {e}. Falling back to standard analysis.")
            return self.analyze(state)


    def review_others(self, reports: dict[str, AgentReport]) -> None:
        """Delegation handled by DeliberationOrchestrator. See Orchestrator.run_review()."""
        pass

        # Check CTO's feasibility and CFO's budget against the marketing strategy.
        cto_report = reports.get("cto")
        cfo_report = reports.get("cfo")

        if cto_report and cfo_report:
            print(f"Alignment Check: Marketing focus must respect technical feasibility ({cto_report.recommendations[0]}) and budget constraints ({cfo_report.recommendations[0]}).")
            # Placeholder for deeper conflict resolution logic
        else:
             print("Warning: Missing technical or financial reports; market strategy lacks necessary context.")

        # The CMO ensures the proposed plan is commercially executable.
