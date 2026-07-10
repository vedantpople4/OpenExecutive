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
            from openexec.ai import AIClient, get_agent_system_prompt, build_analysis_prompt
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
                from openexec.ai import build_analysis_prompt

                prompt = build_analysis_prompt(
                    core_prompt=state.core_prompt,
                    data_corpus=state.data_corpus,
                    agent_name="cto",
                    assumptions=state.assumptions if hasattr(state, 'assumptions') else None,
                    research_cfg=getattr(state, 'research_cfg', None),
                )

                response_data = self.ai_client.complete_json_with_retry(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    temperature=0.7
                )

                return AgentReport.from_llm_response("cto", response_data)
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

        reasoning = {
            "data_used": list(state.data_corpus.keys()),
            "focus_areas": ["Architecture", "Scalability"]
        }

        report = AgentReport(
            title="CTO Technical Feasibility Report",
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks,
            alignment_score=0.8,
            reasoning=reasoning,
            is_fallback=True,
        )
        return report

    def synthesize_team_position(self, team_reports: Dict[str, AgentReport], state: 'SimulationState') -> AgentReport:
        """Synthesize reports from the CTO's team into a consolidated technical position."""
        print("CTO Synthesizing: Consolidating input from Engineering Lead, Architect, and SRE...")

        team_context = "\n\n## INTERNAL TEAM REPORTS\n"
        for member_name, report in team_reports.items():
            team_context += f"\n### {member_name.upper()} Report\n- Summary: {report.summary}\n- Findings: {report.key_findings}\n"

        enhanced_prompt = f"{state.core_prompt}\n\n{team_context}\n\n" \
                         "Review the reports from your specialized technical team. Synthesize their findings " \
                         "into a single, cohesive technical position for the board."

        system_prompt = self.system_prompt + "\n\nMODALITY: You are now synthesizing team input. " \
                                           "Ensure the final output reflects the team's technical research."

        try:
            response_data = self.ai_client.complete_json_with_retry(
                prompt=enhanced_prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            return AgentReport.from_llm_response("cto", response_data)
        except Exception as e:
            print(f"CTO Synthesis failed: {e}. Falling back to standard analysis.")
            return self.analyze(state)


    def review_others(self, reports: dict[str, AgentReport]) -> None:
        """Delegation handled by DeliberationOrchestrator. See Orchestrator.run_review()."""
        pass

        # Cross-check with CFO's budget concerns and CMO's market needs.
        cfo_report = reports.get("cfo")
        cmo_report = reports.get("cmo")

        if cfo_report and cmo_report:
            print(f"Alignment Check: Technical recommendations must be cost-effective ({cfo_report.recommendations[0]}) and market-validated ({cmo_report.recommendations[0]}).")
            # Placeholder for deeper conflict resolution logic
        else:
             print("Warning: Missing financial or market reports; technical recommendations lack full context.")

        # The CTO ensures the proposed technical path is both feasible and commercially viable.
