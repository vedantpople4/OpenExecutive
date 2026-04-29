#!/usr/bin/env python3
"""Executive summary generation for OpenExec."""

from typing import Dict, Any


def generate_executive_summary(results: Dict[str, Any]) -> str:
    """Generate a 1-page executive summary from simulation results."""
    lines = []

    lines.append("# Executive Summary")
    lines.append("")

    # Decision
    decision = results['executive_summary'].replace('Executive Board Analysis for: ', '')
    lines.append(f"**Decision:** {decision}")
    lines.append("")

    # Decision Point
    lines.append("## Decision Point")
    lines.append("")
    decision_point = results.get('decision_point', '').replace('Decision required for: ', '')
    lines.append(decision_point)
    lines.append("")

    # Top 5 Recommendations
    lines.append("## Top Recommendations")
    lines.append("")
    all_recs = results.get('synthesized_recommendations', [])
    for i, rec in enumerate(all_recs[:5], 1):
        lines.append(f"{i}. {rec}")
    lines.append("")

    # Top 3 Risks
    lines.append("## Critical Risks")
    lines.append("")
    all_risks = results.get('overall_risk_assessment', [])
    for i, risk in enumerate(all_risks[:3], 1):
        lines.append(f"{i}. {risk}")
    lines.append("")

    # Confidence Scores
    lines.append("## Agent Confidence")
    lines.append("")
    agent_reports = results.get('agent_reports', {})
    for agent_name, report in agent_reports.items():
        confidence = report.get('confidence_score', 0)
        lines.append(f"- **{agent_name.upper()}:** {confidence:.0%}")
    lines.append("")

    # Data Sources
    if results.get('data_sources'):
        lines.append("## Data Sources")
        lines.append("")
        data_sources = results['data_sources']
        lines.append(f"- **Access Rate:** {data_sources.get('access_success_rate', 0):.0%}")
        lines.append(f"- **Timestamp:** {data_sources.get('timestamp', 'Unknown')}")
        lines.append("")

    lines.append("## Next Steps")
    lines.append("")
    action_count = len(all_recs)
    lines.append(f"{action_count} action items identified. See full report for details.")
    lines.append("")

    return '\n'.join(lines)


def write_executive_summary(results: Dict[str, Any], output_path: str) -> None:
    """Write executive summary to file."""
    summary = generate_executive_summary(results)
    with open(output_path, 'w') as f:
        f.write(summary)