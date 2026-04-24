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
            from src.ai import AIClient, get_agent_system_prompt, build_analysis_prompt
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
                from src.ai import build_analysis_prompt

                # Build AI prompt
                prompt = build_analysis_prompt(
                    core_prompt=state.core_prompt,
                    data_corpus=state.data_corpus,
                    agent_name="ceo"
                )

                # Call LLM
                response_data = self.ai_client.complete_json(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    temperature=0.7
                )

                # Parse response into AgentReport
                return AgentReport(
                    title=response_data.get("title", "CEO Strategic Vision Report"),
                    summary=response_data.get("summary", ""),
                    key_findings=response_data.get("key_findings", []),
                    recommendations=response_data.get("recommendations", []),
                    risks=response_data.get("risks", []),
                    confidence_score=float(response_data.get("confidence_score", 0.75)),
                    reasoning=response_data.get("reasoning", {})
                )
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

        report = AgentReport(
            title="CEO Strategic Vision Report",
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks,
            confidence_score=0.75,
            reasoning={
                "data_used": list(state.data_corpus.keys()),
                "focus_areas": ["Vision", "Alignment"]
            }
        )
        return report


    def review_others(self, reports: dict[str, AgentReport]) -> None:
        """CEO reviews other agents for strategic coherence."""
        print("CEO Reviewing: Cross-functional alignment...")

        # High-level check for conflicts between Vision (CEO) and Feasibility/Market (others)
        cfo_report = reports.get("cfo")
        cto_report = reports.get("cto")
        cmo_report = reports.get("cmo")

        if cfo_report and cto_report:
            if hasattr(cfo_report, 'risks') and hasattr(cto_report, 'risks'):
                print("Conflict Check: Financial risk vs. Technical feasibility.")
                # Placeholder for deeper conflict resolution logic
                pass
        elif not cfo_report or not cto_report:
             print("Warning: Missing financial or technical reports; strategic view is incomplete.")

        # The CEO's role is to synthesize these conflicts into a single, coherent narrative.
        if cmo_report:
            print("Alignment Check: Marketing strategy seems to align with the proposed vision.")
