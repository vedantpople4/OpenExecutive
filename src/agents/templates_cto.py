from .interface import AgentReport
from typing import Any


class CTOTemplate:
    """Concrete CTO implementation focusing on Technical Feasibility and Scalability (How to build it?)."""

    name = "cto"
    role = "Chief Technology Officer"
    focus = "How to build it?"

    def __init__(self):
        """Initialize CTO agent with AI client and real-time data fetcher."""
        try:
            from src.ai import AIClient, get_agent_system_prompt, build_analysis_prompt
            from src.data import RealTimeDataFetcher

            self.ai_client = AIClient()
            self.system_prompt = get_agent_system_prompt("cto")
            self.data_fetcher = RealTimeDataFetcher()
            self.use_ai = True
            self.use_real_time_data = False
        except Exception as e:
            print(f"Warning: AI client initialization failed: {e}")
            print("Falling back to hardcoded analysis.")
            self.use_ai = False
            self.use_real_time_data = False

    def analyze(self, state: 'SimulationState') -> AgentReport:
        """CTO analysis - technical feasibility, scalability, architecture."""
        print("CTO Analyzing: Assessing architectural feasibility and scalability...")

        # Fetch real-time technology context
        real_time_context = ""
        sources_summary = {}
        if self.use_real_time_data:
            try:
                print("CTO: Fetching current technology trends...")
                context = self.data_fetcher.get_context_for_decision(state.core_prompt)
                real_time_context = self.data_fetcher.format_context_for_prompt(context)
                sources_summary = self.data_fetcher.get_sources_summary(context)

                # Report data access status
                accessed_count = len(sources_summary.get('sources_accessed', []))
                failed_count = len(sources_summary.get('sources_failed', []))
                success_rate = sources_summary.get('access_success_rate', 0)

                print(f"CTO: Data Access Report - {accessed_count} sources accessed, "
                      f"{failed_count} sources failed, {success_rate:.1%} success rate")

                if failed_count > 0:
                    print(f"CTO: Warning - Failed to access {failed_count} data sources:")
                    for failed_source in sources_summary.get('sources_failed', []):
                        print(f"  ✗ {failed_source}")

            except Exception as e:
                print(f"CTO: Warning - Could not fetch real-time data: {e}")
                real_time_context = ""

        if self.use_ai:
            try:
                from src.ai import build_analysis_prompt

                from src.ai import build_analysis_prompt

                base_prompt = build_analysis_prompt(
                    core_prompt=state.core_prompt,
                    data_corpus=state.data_corpus,
                    agent_name="cto"
                )

                if real_time_context:
                    enhanced_prompt = (
                        f"{base_prompt}\n\n{real_time_context}\n\n"
                        "## Additional Context\n"
                        "Consider current technology trends and infrastructure developments above "
                        "when assessing technical feasibility."
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

                return AgentReport.from_llm_response("cto", response_data)
            except Exception as e:
                print(f"AI analysis failed: {e}")
                print("Falling back to hardcoded analysis.")
                # Fall through to hardcoded analysis

        # Hardcoded fallback analysis
        summary = f"The proposed solution for {state.core_prompt} requires assessing the current system's capacity against projected growth."
        key_findings = [f"Current architecture shows potential bottlenecks related to scaling."]

        # Add real-time context to findings if available
        if real_time_context:
            key_findings.append("ANALYSIS ENHANCED WITH REAL-TIME TECHNOLOGY DATA")
            key_findings.append("Current technology trends and infrastructure developments have been considered")

        if state.data_corpus:
            for filename, content in state.data_corpus.items():
                key_findings.append(f"Data from '{filename}' highlights scalability concerns regarding {content[:100]}...")

        recommendations = [
            "Implement a microservices architecture to decouple scaling bottlenecks.",
            "Mandate end-to-end testing across all proposed data flows before deployment."
        ]

        # Add real-time aware recommendations
        if real_time_context:
            recommendations.append("Monitor current hardware availability and pricing trends")
            recommendations.append("Consider recent cloud infrastructure developments in architecture decisions")

        risks = [
            "Risk of technical debt accumulating if expediency is prioritized over scalable design.",
            "Risk of system failure under peak load due to inadequate infrastructure planning."
        ]

        reasoning = {
            "data_used": list(state.data_corpus.keys()),
            "focus_areas": ["Architecture", "Scalability"]
        }

        if real_time_context:
            reasoning["real_time_data_used"] = True
            reasoning["data_timestamp"] = sources_summary.get("timestamp", "unknown")
            reasoning["sources_accessed"] = sources_summary.get("sources_accessed", [])
            reasoning["sources_failed"] = sources_summary.get("sources_failed", [])
            reasoning["all_available_sources"] = sources_summary.get("all_available_sources", [])

        report = AgentReport(
            title="CTO Technical Feasibility Report",
            summary=summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks,
            alignment_score=0.8,
            reasoning=reasoning
        )
        return report


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
