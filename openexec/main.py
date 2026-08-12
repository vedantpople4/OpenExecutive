#!/usr/bin/env python3
"""Report rendering for OpenExec.

The legacy CLI that lived here (run_simulation, main, kb/feedback/history
commands) was removed — the Typer CLI in openexec/cli.py is the single entry
point. This module keeps only ``write_report()``, the shared markdown renderer
that cli.py imports.
"""

from typing import Any

from openexec.utils import extract_action_items


def write_report(results: dict[str, Any], output_path: str) -> None:
    """Write the final report to a markdown file."""
    with open(output_path, 'w') as f:
        f.write("# Executive Board Simulation Report\n\n")
        summary = results.get('executive_summary', '')
        if summary:
            f.write(f"## Executive Summary\n\n{summary}\n\n")

        if results.get('fallback_warnings'):
            f.write("## ⚠️ Data Integrity Warning\n\n")
            f.write(
                "The AI model failed to respond for the reports listed below. Each one is a "
                "**hardcoded placeholder stub**, not a real analysis — treat its content as "
                "absent, not as a genuine executive position:\n\n"
            )
            for warning in results['fallback_warnings']:
                f.write(f"- {warning}\n")
            f.write("\n")

        if results.get('decision_point'):
            f.write(f"## Decision Point\n\n{results['decision_point']}\n\n")

        # Board Decision (from CEO round-5 synthesis)
        if results.get('board_decision'):
            bd = results['board_decision']
            f.write("## Board Decision\n\n")
            if bd.get('summary'):
                f.write(f"{bd['summary']}\n\n")
            if bd.get('consensus_points'):
                f.write("### Consensus Points\n\n")
                for pt in bd['consensus_points']:
                    f.write(f"- {pt}\n")
                f.write("\n")
            if bd.get('final_priority_actions'):
                f.write("### Final Priority Actions\n\n")
                for action in bd['final_priority_actions']:
                    f.write(f"- {action}\n")
                f.write("\n")
            if bd.get('dissent_points'):
                f.write("### Dissenting Points\n\n")
                for d in bd['dissent_points']:
                    f.write(f"- {d}\n")
                f.write("\n")
            if bd.get('dissenting_opinions'):
                f.write("### Dissenting Opinions\n\n")
                for d in bd['dissenting_opinions']:
                    f.write(f"- {d}\n")
                f.write("\n")
            if bd.get('contingencies'):
                f.write("### Contingencies\n\n")
                for c in bd['contingencies']:
                    f.write(f"- {c}\n")
                f.write("\n")

        # Deliberation Transcript (rounds 1-5)
        if results.get('deliberation_rounds'):
            f.write("## Deliberation Transcript\n\n")
            for round_num in sorted(results['deliberation_rounds'].keys()):
                round_reports = results['deliberation_rounds'][round_num]
                f.write(f"### Round {round_num}\n\n")
                for agent, report in round_reports.items():
                    f.write(f"**{agent.upper()}**  ")
                    if report.get('round_number'):
                        f.write(f"(Round {report['round_number']})")
                    f.write("\n\n")
                    if report.get('is_fallback'):
                        f.write(
                            "> ⚠️ **FALLBACK STUB — AI call failed this round. "
                            "The content below is a generic placeholder, not a real position.**\n\n"
                        )
                    # R5: board_decision nested content — always render if present
                    bd = report.get('board_decision')
                    if report.get('summary'):
                        f.write(f"{report['summary']}\n\n")
                    elif bd and bd.get('summary'):
                        f.write(f"{bd['summary']}\n\n")
                    if bd:
                        if bd.get('consensus_points'):
                            f.write("**Consensus:**\n")
                            for pt in bd['consensus_points']:
                                f.write(f"- {pt}\n")
                            f.write("\n")
                        if bd.get('dissent_points'):
                            f.write("**Dissent:**\n")
                            for d in bd['dissent_points']:
                                f.write(f"- {d}\n")
                            f.write("\n")
                        if bd.get('final_priority_actions'):
                            f.write("**Priority Actions:**\n")
                            for a in bd['final_priority_actions']:
                                f.write(f"- {a}\n")
                            f.write("\n")
                        if bd.get('contingencies'):
                            f.write("**Contingencies:**\n")
                            for c in bd['contingencies']:
                                f.write(f"- {c}\n")
                            f.write("\n")
                        if bd.get('dissenting_opinions'):
                            f.write("**Dissenting Opinions:**\n")
                            for d in bd['dissenting_opinions']:
                                f.write(f"- {d}\n")
                            f.write("\n")
                    if report.get('agreements'):
                        f.write("**Agreements:**\n")
                        for a in report['agreements']:
                            f.write(f"- {a}\n")
                        f.write("\n")
                    if report.get('conflicts'):
                        f.write("**Conflicts:**\n")
                        for c in report['conflicts']:
                            f.write(f"- {c}\n")
                        f.write("\n")
                    if report.get('required_changes'):
                        f.write("**Required Changes:**\n")
                        for ch in report['required_changes']:
                            f.write(f"- {ch}\n")
                        f.write("\n")
                    if report.get('revised_recommendations'):
                        f.write("**Revised Recommendations:**\n")
                        for rev in report['revised_recommendations']:
                            f.write(f"- {rev}\n")
                        f.write("\n")
                    if report.get('key_findings'):
                        f.write("**Key Findings:**\n")
                        for find in report['key_findings']:
                            f.write(f"- {find}\n")
                        f.write("\n")
                    if report.get('risks'):
                        f.write("**Risks:**\n")
                        for risk in report['risks']:
                            f.write(f"- {risk}\n")
                        f.write("\n")
                f.write("---\n\n")

        f.write("## Individual Agent Reports\n\n")

        for agent_name, report in results.get('agent_reports', {}).items():
            f.write(f"### {agent_name.upper()} Report\n\n")
            if report.get('is_fallback'):
                f.write(
                    "> ⚠️ **FALLBACK STUB — AI analysis failed for this agent. "
                    "The content below is a generic placeholder, not a real recommendation.**\n\n"
                )
            f.write(f"**{report['title']}**\n\n")
            f.write(f"{report['summary']}\n\n")

            if report.get('key_findings'):
                f.write("#### Key Findings\n\n")
                for finding in report['key_findings']:
                    f.write(f"- {finding}\n")
                f.write("\n")

            if report.get('recommendations'):
                f.write("#### Recommendations\n\n")
                for rec in report['recommendations']:
                    f.write(f"- {rec}\n")
                f.write("\n")

            if report.get('risks'):
                f.write("#### Risks\n\n")
                for risk in report['risks']:
                    f.write(f"- {risk}\n")
                f.write("\n")

            grounding = report.get('grounding')
            if grounding and grounding.get('claims_checked'):
                line = (f"**Grounding:** {grounding['claims_grounded']}/{grounding['claims_checked']} "
                        "numeric claims found in source data")
                if grounding.get('ungrounded'):
                    line += f" — unverified: {', '.join(grounding['ungrounded'][:5])}"
                f.write(f"{line}\n\n")

            score = report['alignment_score']
            if score >= 0.8:
                interpretation = "High confidence (data is solid)"
            elif score >= 0.5:
                interpretation = "Moderate confidence (some uncertainty)"
            else:
                interpretation = "Low confidence (thin data, high uncertainty)"
            f.write(f"**Alignment Score:** {score:.2f} — {interpretation}\n\n")
            f.write("---\n\n")

        if results.get('synthesized_recommendations'):
            f.write("## Synthesized Recommendations\n\n")
            for rec in results['synthesized_recommendations']:
                f.write(f"- {rec}\n")
            f.write("\n")

        # Extract action items from recommendations
        f.write("## Action Items\n\n")
        action_items = extract_action_items(results)
        if action_items:
            for item in action_items:
                priority = item.get('priority', 'MEDIUM')
                task = item.get('task', 'No task specified')
                owner = item.get('owner', 'Unassigned')
                due_date = item.get('due_date', 'TBD')
                f.write(f"- [{priority}] {task} (Owner: {owner}, Due: {due_date})\n")
        else:
            f.write("No action items identified.\n")
        f.write("\n")

        if results.get('overall_risk_assessment'):
            f.write("## Overall Risk Assessment\n\n")
            for risk in results['overall_risk_assessment']:
                f.write(f"- {risk}\n")
            f.write("\n")

        if results.get('risk_matrix'):
            f.write("## Risk Quantification\n\n")
            f.write(results['risk_matrix'])
            f.write("\n")

        if results.get('data_sources'):
            f.write("## Data Sources\n\n")
            data_sources = results['data_sources']

            f.write(f"**Data Fetch Timestamp:** {data_sources.get('timestamp', 'Unknown')}\n\n")
            f.write(f"**Access Success Rate:** {data_sources.get('access_success_rate', 0):.1%}\n\n")

            if data_sources.get('sources_accessed'):
                f.write("### Successfully Accessed Sources\n\n")
                for source in data_sources['sources_accessed']:
                    f.write(f"- {source}\n")
                f.write("\n")

            if data_sources.get('sources_failed'):
                f.write("### Failed to Access Sources\n\n")
                for source in data_sources['sources_failed']:
                    f.write(f"- {source}\n")
                f.write("\n")

            if data_sources.get('all_available_sources'):
                f.write("### All Available Data Sources\n\n")
                for source in data_sources['all_available_sources']:
                    f.write(f"- {source}\n")
                f.write("\n")

            if data_sources.get('research_sources_consulted'):
                f.write("### Research Sources Consulted (--research)\n\n")
                f.write("Fetched programmatically via live web search / knowledge base "
                        "retrieval -- not self-reported by the model.\n\n")
                for source in data_sources['research_sources_consulted']:
                    f.write(f"- {source}\n")
                f.write("\n")