from .interface import AgentReport
from typing import Any
import json


class CEOTemplate:
    """Concrete CEO implementation focusing on Vision and Strategy (Why?)."""

    name = "ceo"
    role = "Chief Executive Officer"
    focus = "Why?"

    def __init__(self):
        """Initialize CEO agent with AI client and real-time data fetcher."""
        try:
            from openexec.ai import AIClient, get_agent_system_prompt, build_analysis_prompt
            from openexec.data import RealTimeDataFetcher

            self.ai_client = AIClient()
            self.system_prompt = get_agent_system_prompt("ceo")
            self.data_fetcher = RealTimeDataFetcher()
            self.use_ai = True
            self.use_real_time_data = False
        except Exception as e:
            print(f"Warning: AI client initialization failed: {e}")
            print("Falling back to hardcoded analysis.")
            self.use_ai = False
            self.use_real_time_data = False

    def analyze(self, state: 'SimulationState') -> AgentReport:
        """CEO analysis - define vision, strategic direction, high-level goals."""
        print("CEO Analyzing: Defining the overarching strategic direction...")

        # Fetch real-time market context
        real_time_context = ""
        sources_summary = {}
        if self.use_real_time_data:
            try:
                print("CEO: Fetching current market intelligence...")
                context = self.data_fetcher.get_context_for_decision(state.core_prompt)
                real_time_context = self.data_fetcher.format_context_for_prompt(context)
                sources_summary = self.data_fetcher.get_sources_summary(context)

                # Report data access status
                accessed_count = len(sources_summary.get('sources_accessed', []))
                failed_count = len(sources_summary.get('sources_failed', []))
                success_rate = sources_summary.get('access_success_rate', 0)

                print(f"CEO: Data Access Report - {accessed_count} sources accessed, "
                      f"{failed_count} sources failed, {success_rate:.1%} success rate")

                if failed_count > 0:
                    print(f"CEO: Warning - Failed to access {failed_count} data sources:")
                    for failed_source in sources_summary.get('sources_failed', []):
                        print(f"  ✗ {failed_source}")

            except Exception as e:
                print(f"CEO: Warning - Could not fetch real-time data: {e}")
                real_time_context = ""

        if self.use_ai:
            try:
                from openexec.ai import build_analysis_prompt

                base_prompt = build_analysis_prompt(
                    core_prompt=state.core_prompt,
                    data_corpus=state.data_corpus,
                    agent_name="ceo",
                    assumptions=state.assumptions if hasattr(state, 'assumptions') else None
                )

                if real_time_context:
                    enhanced_prompt = (
                        f"{base_prompt}\n\n{real_time_context}\n\n"
                        "## Additional Context\n"
                        "Consider current market trends and recent developments above "
                        "when formulating your strategic analysis."
                    )
                else:
                    enhanced_prompt = base_prompt

                response_data = self.ai_client.complete_json_with_retry(
                    prompt=enhanced_prompt,
                    system_prompt=self.system_prompt,
                    temperature=0.7
                )

                reasoning = response_data.get("reasoning", {})
                if real_time_context:
                    reasoning["real_time_data_used"] = True
                    reasoning["data_timestamp"] = context.get("timestamp", "unknown")
                    reasoning.update(sources_summary)
                response_data["reasoning"] = reasoning

                return AgentReport.from_llm_response("ceo", response_data)
            except Exception as e:
                print(f"AI analysis failed: {e}")
                print("Falling back to hardcoded analysis.")
                # Fall through to hardcoded analysis

        # Hardcoded fallback analysis
        summary = f"The core problem is {state.core_prompt}. The goal is to determine the optimal path forward given the provided Data Corpus."
        key_findings = [f"Core conflict: {state.core_prompt}"]

        # Add real-time context to findings if available
        if real_time_context:
            key_findings.append("ANALYSIS ENHANCED WITH REAL-TIME MARKET DATA")
            key_findings.append("Current market conditions have been considered in this analysis")

        if state.data_corpus:
            for filename, content in state.data_corpus.items():
                key_findings.append(f"Data from '{filename}' suggests: {content[:100]}...")

        recommendations = [
            "Prioritize alignment between the financial constraints (CFO) and the technological feasibility (CTO).",
            "Focus initial strategy on the market fit identified by the CMO data."
        ]

        # Add real-time aware recommendations
        if real_time_context:
            recommendations.append("Monitor current market trends for competitive positioning")
            recommendations.append("Consider recent industry developments in strategic planning")

        risks = [
            "Risk of strategic misalignment if technical debt is ignored.",
            "Risk of poor market adoption if marketing strategy is disconnected from product reality."
        ]

        reasoning = {
            "data_used": list(state.data_corpus.keys()),
            "focus_areas": ["Vision", "Alignment"]
        }

        if real_time_context:
            reasoning["real_time_data_used"] = True
            reasoning["data_timestamp"] = sources_summary.get("timestamp", "unknown")
            reasoning["sources_accessed"] = sources_summary.get("sources_accessed", [])
            reasoning["sources_failed"] = sources_summary.get("sources_failed", [])
            reasoning["all_available_sources"] = sources_summary.get("all_available_sources", [])

        report = AgentReport(
            title="CEO Strategic Vision Report",
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks,
            alignment_score=0.75,
            reasoning=reasoning
        )
        return report


    def review_others(self, reports: dict[str, AgentReport]) -> None:
        """Delegation handled by DeliberationOrchestrator. See Orchestrator.run_review()."""
        pass
