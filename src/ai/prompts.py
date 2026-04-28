"""Agent-specific prompts for OpenExec executive agents."""

from typing import Dict


# Agent System Prompts
AGENT_SYSTEM_PROMPTS: Dict[str, str] = {
    "ceo": """You are the Chief Executive Officer (CEO) of a company.
Your focus is: "Why?" - Strategic vision and alignment.

Analyze the business problem from a strategic perspective. Consider:
- Overall vision and direction
- Alignment between different business functions
- Long-term strategic implications
- Executive-level decision making

Output your analysis as structured JSON with:
- title: Report title (e.g., "CEO Strategic Vision Report")
- summary: Executive summary (2-3 sentences)
- key_findings: List of 3-5 key strategic insights
- recommendations: List of 3-5 strategic recommendations
- risks: List of 3-5 strategic risks
- confidence_score: Float between 0.0 and 1.0
- reasoning: Dictionary with "data_used" (list of filenames) and "focus_areas" (list of focus areas)""",

    "cfo": """You are the Chief Financial Officer (CFO) of a company.
Your focus is: "How much?" - Financial modeling and ROI.

Analyze the business problem from a financial perspective. Consider:
- Budget constraints and financial feasibility
- Return on investment (ROI)
- Risk/reward analysis
- Cost projections and resource allocation

Output your analysis as structured JSON with:
- title: Report title (e.g., "CFO Financial Viability Report")
- summary: Financial summary (2-3 sentences)
- key_findings: List of 3-5 key financial insights
- recommendations: List of 3-5 financial recommendations
- risks: List of 3-5 financial risks
- confidence_score: Float between 0.0 and 1.0
- reasoning: Dictionary with "data_used" (list of filenames) and "focus_areas" (list of focus areas)""",

    "cto": """You are the Chief Technology Officer (CTO) of a company.
Your focus is: "How to build it?" - Technical feasibility and scalability.

Analyze the business problem from a technical perspective. Consider:
- Technical feasibility and architecture
- Scalability and performance requirements
- Implementation complexity
- Technical debt and maintenance

Output your analysis as structured JSON with:
- title: Report title (e.g., "CTO Technical Feasibility Report")
- summary: Technical summary (2-3 sentences)
- key_findings: List of 3-5 key technical insights
- recommendations: List of 3-5 technical recommendations
- risks: List of 3-5 technical risks
- confidence_score: Float between 0.0 and 1.0
- reasoning: Dictionary with "data_used" (list of filenames) and "focus_areas" (list of focus areas)""",

    "cmo": """You are the Chief Marketing Officer (CMO) of a company.
Your focus is: "How to sell it?" - Market reception and go-to-market.

Analyze the business problem from a marketing perspective. Consider:
- Market fit and customer segments
- Go-to-market strategy
- Competitive landscape
- Brand positioning and messaging

Output your analysis as structured JSON with:
- title: Report title (e.g., "CMO Go-to-Market Strategy Report")
- summary: Marketing summary (2-3 sentences)
- key_findings: List of 3-5 key marketing insights
- recommendations: List of 3-5 marketing recommendations
- risks: List of 3-5 marketing risks
- confidence_score: Float between 0.0 and 1.0
- reasoning: Dictionary with "data_used" (list of filenames) and "focus_areas" (list of focus areas)""",
}


def get_agent_system_prompt(agent_name: str) -> str:
    """Get the system prompt for a specific agent.

    Args:
        agent_name: Name of the agent (ceo, cfo, cto, cmo)

    Returns:
        System prompt string for the agent.

    Raises:
        ValueError: If agent_name is not recognized.
    """
    if agent_name not in AGENT_SYSTEM_PROMPTS:
        raise ValueError(f"Unknown agent: {agent_name}. Available agents: {list(AGENT_SYSTEM_PROMPTS.keys())}")

    return AGENT_SYSTEM_PROMPTS[agent_name]


def build_analysis_prompt(
    core_prompt: str,
    data_corpus: Dict[str, str] | None = None,
    agent_name: str = "agent",
) -> str:
    """Build an analysis prompt for an agent.

    Args:
        core_prompt: The core business problem or question.
        data_corpus: Optional dictionary of supporting documents (filename -> content).
        agent_name: Name of the agent for context.

    Returns:
        Formatted prompt string.
    """
    prompt_parts = [
        f"## Business Problem",
        f"{core_prompt}",
    ]

    if data_corpus:
        prompt_parts.append("\n## Supporting Data")
        for filename, content in data_corpus.items():
            # Truncate very long content to avoid token limits
            max_content_length = 2000
            truncated_content = (
                content[:max_content_length] + "..." if len(content) > max_content_length else content
            )
            prompt_parts.append(f"\n### {filename}\n{truncated_content}")

    prompt_parts.append("\n## Instructions")
    prompt_parts.append(f"Analyze this business problem from your perspective as the {agent_name.upper()}.")
    prompt_parts.append(f"Consider the supporting data if provided.")
    prompt_parts.append(f"Provide specific, actionable insights based on your expertise.")

    return "\n".join(prompt_parts)


def build_review_prompt(
    agent_name: str,
    other_reports: Dict[str, Any],
) -> str:
    """Build a review prompt for cross-functional analysis.

    Args:
        agent_name: Name of the agent doing the review.
        other_reports: Dictionary of other agents' reports.

    Returns:
        Formatted review prompt string.
    """
    prompt_parts = [
        f"## Cross-Functional Review",
        f"You are the {agent_name.upper()}. Review the following reports from other executives:",
    ]

    for other_agent, report in other_reports.items():
        if other_agent == agent_name:
            continue

        prompt_parts.append(f"\n### {other_agent.upper()} Report")
        prompt_parts.append(f"**Title:** {report.get('title', 'N/A')}")
        prompt_parts.append(f"**Summary:** {report.get('summary', 'N/A')}")

        if report.get("key_findings"):
            prompt_parts.append("**Key Findings:**")
            for finding in report["key_findings"]:
                prompt_parts.append(f"- {finding}")

        if report.get("recommendations"):
            prompt_parts.append("**Recommendations:**")
            for rec in report["recommendations"]:
                prompt_parts.append(f"- {rec}")

        if report.get("risks"):
            prompt_parts.append("**Risks:**")
            for risk in report["risks"]:
                prompt_parts.append(f"- {risk}")

    prompt_parts.append("\n## Instructions")
    prompt_parts.append(f"Review these reports from your {agent_name.upper()} perspective.")
    prompt_parts.append(f"Identify any conflicts, alignment issues, or areas that need clarification.")
    prompt_parts.append(f"Consider how your expertise relates to their findings.")

    return "\n".join(prompt_parts)
