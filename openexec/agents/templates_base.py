"""Shared CXO template base — the analyze/synthesize pipeline is identical
across the four executives; only role metadata, fallback content, and
synthesis wording differ. Keeps per-role drift from silently diverging (the
fallback paths used to be copy-pasted four times)."""

from typing import TYPE_CHECKING, Dict

from .interface import AgentReport

if TYPE_CHECKING:
    from openexec.orchestrator import SimulationState


class AgentTemplate:
    """Base class for the four CXO agents.

    Subclasses set role metadata and fallback content via class attributes;
    analyze() and synthesize_team_position() are inherited.
    """

    name = ""
    role = ""
    focus = ""
    analyze_msg = ""
    fallback_title = ""
    fallback_alignment = 0.5
    fallback_focus_areas: list[str] = []
    fallback_recommendations: list[str] = []
    fallback_risks: list[str] = []

    def __init__(self):
        """Initialize CXO agent with AI client, falling back to hardcoded."""
        try:
            from openexec.ai import AIClient, get_agent_system_prompt
            self.ai_client = AIClient()
            self.system_prompt = get_agent_system_prompt(self.name)
            self.use_ai = True
        except Exception as e:
            print(f"Warning: AI client initialization failed: {e}")
            print("Falling back to hardcoded analysis.")
            self.use_ai = False

    # ------------------------------------------------------------------
    # Per-role fallback content hooks
    # ------------------------------------------------------------------

    def _fallback_summary(self, state) -> str:
        raise NotImplementedError

    def _fallback_findings(self, state) -> list[str]:
        raise NotImplementedError

    def _build_fallback_report(self, state) -> AgentReport:
        return AgentReport(
            title=self.fallback_title,
            summary=self._fallback_summary(state),
            key_findings=self._fallback_findings(state),
            recommendations=list(self.fallback_recommendations),
            risks=list(self.fallback_risks),
            alignment_score=self.fallback_alignment,
            reasoning={
                "data_used": list(state.data_corpus.keys()),
                "focus_areas": self.fallback_focus_areas,
            },
            is_fallback=True,
        )

    # ------------------------------------------------------------------
    # Shared analyze pipeline
    # ------------------------------------------------------------------

    def analyze(self, state: "SimulationState") -> AgentReport:
        print(self.analyze_msg)

        if self.use_ai:
            try:
                from openexec.ai import build_analysis_prompt

                prompt = build_analysis_prompt(
                    core_prompt=state.core_prompt,
                    data_corpus=state.data_corpus,
                    agent_name=self.name,
                    assumptions=state.assumptions if hasattr(state, 'assumptions') else None,
                    research_cfg=getattr(state, 'research_cfg', None),
                    past_decisions_context=getattr(state, 'past_decisions_context', '') or None,
                )

                response_data = self.ai_client.complete_json_with_retry(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    temperature=0.7
                )

                return AgentReport.from_llm_response(self.name, response_data)
            except Exception as e:
                print(f"AI analysis failed: {e}")
                print("Falling back to hardcoded analysis.")

        return self._build_fallback_report(state)

    # ------------------------------------------------------------------
    # Shared team-position synthesis
    # ------------------------------------------------------------------

    _SYNTHESIZE_MODALITY = "Ensure the final output reflects the team's research."

    def synthesize_team_position(self, team_reports: Dict[str, AgentReport], state: "SimulationState") -> AgentReport:
        """Synthesize reports from the CXO's team into a consolidated position."""
        team_context = "\n\n## INTERNAL TEAM REPORTS\n"
        for member_name, report in team_reports.items():
            team_context += f"\n### {member_name.upper()} Report\n- Summary: {report.summary}\n- Findings: {report.key_findings}\n"

        enhanced_prompt = f"{state.core_prompt}\n\n{team_context}\n\n" \
                         "Review the reports from your specialized team. Synthesize their findings " \
                         "into a single, cohesive position for the board."

        system_prompt = self.system_prompt + "\n\nMODALITY: You are now synthesizing team input. " \
                                           + self._SYNTHESIZE_MODALITY

        try:
            response_data = self.ai_client.complete_json_with_retry(
                prompt=enhanced_prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )
            return AgentReport.from_llm_response(self.name, response_data)
        except Exception as e:
            print(f"{self.name.upper()} Synthesis failed: {e}. Falling back to standard analysis.")
            return self.analyze(state)

    def review_others(self, reports: dict[str, AgentReport]) -> None:
        """Delegation handled by DeliberationOrchestrator."""
        pass