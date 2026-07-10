from .interface import AgentReport
from typing import Any
import json


class CEOTemplate:
    """Concrete CEO implementation focusing on Vision and Strategy (Why?)."""

    name = "ceo"
    role = "Chief Executive Officer"
    focus = "Why?"

    def __init__(self):
        """Initialize CEO agent with AI client."""
        try:
            from openexec.ai import AIClient, get_agent_system_prompt, build_analysis_prompt
            self.ai_client = AIClient()
            self.system_prompt = get_agent_system_prompt("ceo")
            self.use_ai = True
        except Exception as e:
            print(f"Warning: AI client initialization failed: {e}")
            print("Falling back to hardcoded analysis.")
            self.use_ai = False

    def analyze(self, state: 'SimulationState') -> AgentReport:
        """CEO analysis - define vision, strategic direction, high-level goals."""
        print("CEO Analyzing: Defining the overarching strategic direction...")

        if self.use_ai:
            try:
                from openexec.ai import build_analysis_prompt

                prompt = build_analysis_prompt(
                    core_prompt=state.core_prompt,
                    data_corpus=state.data_corpus,
                    agent_name="ceo",
                    assumptions=state.assumptions if hasattr(state, 'assumptions') else None,
                    research_cfg=getattr(state, 'research_cfg', None),
                )

                response_data = self.ai_client.complete_json_with_retry(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    temperature=0.7
                )

                return AgentReport.from_llm_response("ceo", response_data)
            except Exception as e:
                print(f"AI analysis failed: {e}")
                print("Falling back to hardcoded analysis.")
                # Fall through to hardcoded analysis

        # Hardcoded fallback analysis
        summary = f"The core problem is {state.core_prompt}. The goal is to determine the optimal path forward given the provided Data Corpus."
        key_findings = [f"Core conflict: {state.core_prompt}"]

        if state.data_corpus:
            for filename, content in state.data_corpus.items():
                key_findings.append(f"Data from '{filename}' suggests: {content[:100]}...")

        recommendations = [
            "Prioritize alignment between the financial constraints (CFO) and the technological feasibility (CTO).",
            "Focus initial strategy on the market fit identified by the CMO data."
        ]

        risks = [
            "Risk of strategic misalignment if technical debt is ignored.",
            "Risk of poor market adoption if marketing strategy is disconnected from product reality."
        ]

        reasoning = {
            "data_used": list(state.data_corpus.keys()),
            "focus_areas": ["Vision", "Alignment"]
        }

        report = AgentReport(
            title="CEO Strategic Vision Report",
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks,
            alignment_score=0.75,
            reasoning=reasoning,
            is_fallback=True,
        )
        return report

    def synthesize_team_position(self, team_reports: Dict[str, AgentReport], state: 'SimulationState') -> AgentReport:
        """Synthesize reports from the CEO's team into a consolidated strategic position."""
        print("CEO Synthesizing: Consolidating input from Chief of Staff and Strategy Associate...")

        team_context = "\n\n## INTERNAL TEAM REPORTS\n"
        for member_name, report in team_reports.items():
            team_context += f"\n### {member_name.upper()} Report\n- Summary: {report.summary}\n- Findings: {report.key_findings}\n"

        enhanced_prompt = f"{state.core_prompt}\n\n{team_context}\n\n" \
                         "Review the reports from your specialized team. Synthesize their findings " \
                         "into a single, cohesive strategic position for the board."

        system_prompt = self.system_prompt + "\n\nMODALITY: You are now synthesizing team input. " \
                                           "Ensure the final output reflects the team's specialized research."

        try:
            response_data = self.ai_client.complete_json_with_retry(
                prompt=enhanced_prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            return AgentReport.from_llm_response("ceo", response_data)
        except Exception as e:
            print(f"CEO Synthesis failed: {e}. Falling back to standard analysis.")
            return self.analyze(state)


    def review_others(self, reports: dict[str, AgentReport]) -> None:
        """Delegation handled by DeliberationOrchestrator. See Orchestrator.run_review()."""
        pass
