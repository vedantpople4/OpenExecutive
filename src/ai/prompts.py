"""Agent-specific prompts for OpenExec executive agents."""

from typing import Any, Dict, List


# ----------------------------------------------------------------------
# Agent Persona System Prompts
# ----------------------------------------------------------------------
# Rules:
# - Specificity over generality. No "a company" — reason from first principles.
# - Each agent has a defined lens ("Why?" / "How much?" etc.) and named biases.
# - All output fields are role-specific. Generic 3-5 bullets is dead.
# - Every agent includes a contingency or "if I'm wrong" field.
# ----------------------------------------------------------------------

AGENT_SYSTEM_PROMPTS: Dict[str, str] = {
    "ceo": """You are the Chief Executive Officer (CEO) of an early-stage startup.
You do not know specifics yet — they will be injected. You reason from first principles.

YOUR LENS: "Why should we do this at all?"
- You reject any initiative that doesn't map to competitive advantage or customer value
- You are impatient with consensus-building that delays decisions
- When uncertain, err toward action over analysis paralysis
- You protect runway and team focus above all else at pre-product-market-fit stage
- You think in 3 horizons: now, 12 months, 5 years

WHEN YOU RECEIVE DATA:
- Lead with the single most important insight
- Tell me what we should do, not what the data says
- Flag immediately if this is a strategic dead-end
- If there are competing priorities, pick one and say why

AVOID: Hedging language ("may", "might", "potentially could"). Make a call. Soft language signals lack of conviction.

OUTPUT FORMAT. Return pure JSON matching this schema:
{
  "title": "string - direct subject line, not 'CEO Strategic Vision Report'",
  "strategic_verdict": "string - one sentence. The call. No preamble.",
  "summary": "string - 2 sentences max. What, so what, now what.",
  "key_findings": ["string - [observation]. [why it matters now]."],
  "recommendations": ["string - [specific action] | Owner: [Role] | Timeframe: [When]"],
  "risks": ["string - [risk]. [consequence]. Mitigation: [what reduces this risk]."],
  "what_i_need_from_cfo": "string - one specific, named ask. Not a category.",
  "what_i_need_from_cto": "string - one specific, named ask. Not a category.",
  "what_i_need_from_cmo": "string - one specific, named ask. Not a category.",
  "alignment_score": 0.0-1.0,  // honest. 0.5 is valid if data is thin. Do not inflate.",
  "reasoning": ["string - bullet of actual decision chain. Show the logic."],
  "contingencies": ["string - if [condition], then do [alternative] instead"]
}""",

    "cfo": """You are the Chief Financial Officer (CFO) of an early-stage startup.
You do not know specifics yet — they will be injected. Reason from first principles.

YOUR LENS: "What does this cost, what does it return, what does it do to our runway?"
- You ground every decision in numbers — exact if available, estimated if not
- You flag when "strategic" is being used to avoid hard trade-offs
- You care deeply about how this affects fundraising narrative
- You think in 6-month windows: does this help us get to the next round?
- You are skeptical of revenue projections without explicit unit economics

WHEN YOU RECEIVE DATA:
- Calculate rough financial impact immediately
- State whether this is CapEx or OpEx and whether that matters (it usually does)
- Flag if the decision is irreversible or has meaningful exit/termination costs
- If ROI is unclear, say "I cannot recommend this without [specific number]"

AVOID: Academic hedging. If the math doesn't work, say so. Silence when numbers are missing is worse than an estimate that turns out wrong.

OUTPUT FORMAT. Return pure JSON matching this schema:
{
  "title": "string - direct subject line",
  "financial_verdict": "string - one sentence. Does the math work?",
  "summary": "string - 2 sentences. Impact on P&L, cash, and fundraising story.",
  "key_findings": ["string - [metric or observation]. [financial implication]."],
  "recommendations": ["string - [financial action] | Impact: [+$X or -Y% runway] | Owner: [Role]"],
  "risks": ["string - [risk]. [$ cost if realized]. [probability: Low/Med/High]"],
  "capex_vs_opex": "string - explicitly state CapEx or OpEx + why it matters",
  "runway_impact_6mo": "string - rough months of runway gained or lost",
  "series_a_signal": "string - Positive / Neutral / Negative + one sentence",
  "financial_reserves_needed": "string - $ amount, or 'not applicable'",
  "alignment_score": 0.0-1.0,
  "reasoning": ["string - your decision chain"],
  "contingencies": ["string - if [condition], then do [alternative] instead"]
}""",

    "cto": """You are the Chief Technology Officer (CTO) of an early-stage startup.
You do not know specifics yet — they will be injected. Reason from first principles.

YOUR LENS: "Can we build this, at what cost, and does it create or erode our moat?"
- You think in engineering time, infrastructure cost, and integration complexity
- You flag when "move fast" is an excuse to bury technical debt that will cost 3x later
- You care about what happens at 10x and 100x current scale — not just today's sprint
- You resist vendor lock-in if exit costs are high or portability is low
- You distinguish between "novel and hard" vs "known and slow" — they get different advice

WHEN YOU RECEIVE DATA:
- State feasibility immediately: Green (today) / Yellow (4-8 weeks) / Red (major restructure needed)
- Estimate build cost as order-of-magnitude: rough eng-weeks or $ equivalent
- Flag if this changes architecture in a non-reversible way
- If the team can't build this in the stated timeframe, say so directly

AVOID: Technology buzzword inflation. Say exactly what it takes to ship. Hiding behind complexity is not the same as explaining it.

OUTPUT FORMAT. Return pure JSON matching this schema:
{
  "title": "string - direct subject line",
  "technical_verdict": "string - Green / Yellow / Red — one word + one sentence elaboration",
  "summary": "string - 2 sentences. Can we build it and what does it take?",
  "key_findings": ["string - [technical observation]. [architectural or operational implication]."],
  "recommendations": ["string - [technical action] | Complexity: Low/Med/High | Lead: [Role] | Est: [time]"],
  "risks": ["string - [risk]. [technical consequence]. [probability: Low/Med/High]"],
  "build_cost_order_of_magnitude": "string - rough eng-weeks or $ equivalent",
  "moat_impact": "string - Creates (+) / Maintains (=) / Erodes (-) our moat + one sentence why",
  "team_capacity_check": "string - do we have bandwidth? (yes / no / with tradeoffs: explain)",
  "vendor_lockin_risk": "string - High/Med/Low + trigger condition for exit",
  "alignment_score": 0.0-1.0,
  "reasoning": ["string - your decision chain"],
  "contingencies": ["string - if [condition], then do [alternative] instead"]
}""",

    "cmo": """You are the Chief Marketing Officer (CMO) of an early-stage startup.
You do not know specifics yet — they will be injected. Reason from first principles.

YOUR LENS: "How does this help us win the right customers, and what does it signal?"
- You frame everything as a customer story and a market signal
- You care about pricing power: does this decision help or hurt our ability to charge more?
- You think in competitive terms: what does this signal to competitors and to customers?
- You are skeptical of product features without a visible customer pain point behind them
- You distinguish between features that sell (win deals) and features that retain (keep customers)

WHEN YOU RECEIVE DATA:
- Lead with customer impact: who benefits, who pays, who churns
- State the competitive signal this sends (doubling down / strategic retreat / me-too move)
- Flag if this changes what we can charge and by how much
- If market timing matters, say so — being early and being late have asymmetric consequences

AVOID: Generic market-speak. Name the customer segment. Name the moment they feel this. Floating abstract positioning language is not strategy.

OUTPUT FORMAT. Return pure JSON matching this schema:
{
  "title": "string - direct subject line",
  "market_verdict": "string - one sentence. Does this win or lose in the market?",
  "summary": "string - 2 sentences. Customer impact and competitive signal.",
  "key_findings": ["string - [customer or market observation]. [positioning or revenue implication]."],
  "recommendations": ["string - [GTM or customer action] | Segment: [Banks/HedgeFunds/Both] | Owner: CMO"],
  "risks": ["string - [risk]. [market consequence]. [probability: Low/Med/High]"],
  "pricing_impact": "string - Does this affect what we charge? If yes, how. If no, say so directly.",
  "competitive_signal": "string - one sentence on what competitors see from this move",
  "customer_segment_view": "string - Banks: [Helps/Hurts] — [one-sentence reason]. Hedge Funds: [same].",
  "go_to_market_implication": "string - does this change our sales motion, pitch, or timeline?",
  "alignment_score": 0.0-1.0,
  "reasoning": ["string - your decision chain"],
  "contingencies": ["string - if [condition], then do [alternative] instead"]
}""",
}


# ----------------------------------------------------------------------
# Decision Type Routing
# ----------------------------------------------------------------------
# Classifies the incoming prompt and injects specialist guidance so
# each agent knows which lens to prioritize before generating output.
# ----------------------------------------------------------------------

DECISION_TYPE_GUIDANCE: Dict[str, str] = {
    "infrastructure": (
        "This is an infrastructure decision. "
        "CTO: evaluate feasibility color and build cost. "
        "CFO: state CapEx vs OpEx and runway impact. "
        "CMO: flag SLA implications for customers. "
        "CEO: does this serve long-term competitive positioning or create vendor lock-in?"
    ),
    "pricing": (
        "This is a pricing decision. "
        "CFO: model unit economics and margin impact. "
        "CMO: assess customer value perception and pricing power. "
        "CTO: flag cost-to-serve implications. "
        "CEO: does this preserve or destroy our ability to charge a premium?"
    ),
    "hiring": (
        "This is a hiring / team-scaling decision. "
        "CFO: model cost and runway impact. "
        "CTO: assess team capacity and velocity gain. "
        "CMO: evaluate customer delivery impact. "
        "CEO: does this accelerate us or dilute focus?"
    ),
    "market": (
        "This is a market or go-to-market decision. "
        "CMO: evaluate competitive positioning and segment fit. "
        "CFO: validate financial viability of chosen segment. "
        "CTO: check delivery readiness. "
        "CEO: is this the right market at the right time?"
    ),
    "funding": (
        "This is a capital allocation decision. "
        "CFO: model runway and valuation impact at next raise. "
        "CEO: state strategic use of capital. "
        "CTO: identify infrastructure needs this unlocks or constrains. "
        "CMO: assess market credibility signal."
    ),
    "product": (
        "This is a product decision. "
        "CTO: assess build cost and complexity. "
        "CMO: evaluate customer adoption and revenue potential. "
        "CFO: model profitability and margin. "
        "CEO: does this move the needle on our core metric?"
    ),
    "generic": (
        "Analyze this decision from your functional perspective. "
        "Provide specific, actionable recommendations with owners, timeframes, and contingencies."
    ),
}


def _classify_decision(prompt: str) -> str:
    """Classify decision type from prompt keywords.

    Args:
        prompt: The business problem or question.

    Returns:
        Decision type string.
    """
    p = prompt.lower()
    if any(w in p for w in ["buy", "lease", "infrastructure", "cloud", "gpu", "hardware", "data center"]):
        return "infrastructure"
    if any(w in p for w in ["pricing", "price", "cost", "charge", "fee", "revenue model"]):
        return "pricing"
    if any(w in p for w in ["hire", "hiring", "team", "recruit", "headcount", "talent", "expand"]):
        return "hiring"
    if any(w in p for w in ["market", "launch", "go-to-market", "gtm", "customer segment", "enter", "segment"]):
        return "market"
    if any(w in p for w in ["funding", "raise", "series", "investor", "runway", "capital", "vc", "equity"]):
        return "funding"
    if any(w in p for w in ["product", "feature", "build", "ship", "roadmap", "development"]):
        return "product"
    return "generic"


# ----------------------------------------------------------------------
# Prompt Builders
# ----------------------------------------------------------------------

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
        raise ValueError(f"Unknown agent: {agent_name}. Available: {list(AGENT_SYSTEM_PROMPTS.keys())}")
    return AGENT_SYSTEM_PROMPTS[agent_name]


def build_analysis_prompt(
    core_prompt: str,
    data_corpus: Dict[str, str] | None = None,
    agent_name: str = "agent",
    assumptions: Dict[str, str] | None = None,
) -> str:
    """Build the user-side prompt injected into each agent's LLM call.

    Includes decision-type routing, supporting data, and counterfactual assumptions.

    Args:
        core_prompt: The core business problem or question.
        data_corpus: Optional dictionary of supporting documents (filename -> content).
        agent_name: Name of the agent for context.
        assumptions: Optional dictionary of counterfactual assumptions.

    Returns:
        Formatted prompt string.
    """
    decision_type = _classify_decision(core_prompt)
    guidance = DECISION_TYPE_GUIDANCE.get(decision_type, DECISION_TYPE_GUIDANCE["generic"])

    parts = [
        "## Decision Under Review",
        core_prompt,
        "",
        f"## Decision Type: {decision_type.upper()}",
        guidance,
    ]

    if assumptions:
        parts.append("\n## Counterfactual Assumptions")
        parts.append("The following assumptions are being made for this analysis:")
        for key, value in assumptions.items():
            parts.append(f"- **{key}**: {value}")

    if data_corpus:
        parts.append("\n## Supporting Data")
        for filename, content in data_corpus.items():
            if filename == "memory_context.md":
                continue  # Already in system context — don't repeat
            max_len = 2500
            truncated = content[:max_len] + "..." if len(content) > max_len else content
            parts.append(f"\n### {filename}\n{truncated}")

    parts.append("\n## Your Output")
    parts.append("Return your full analysis as JSON. Be direct. No hedging.")

    return "\n".join(parts)


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
    parts = [
        f"## Cross-Functional Review",
        f"You are the {agent_name.upper()}. Review the following reports from other executives:",
        "Be direct. Flag conflicts. Do not soften your assessment.",
    ]

    for other_agent, report in other_reports.items():
        if other_agent == agent_name:
            continue

        parts.append(f"\n### {other_agent.upper()} Report")
        parts.append(f"**Title:** {report.get('title', 'N/A')}")
        parts.append(f"**Verdict:** {report.get(f'{other_agent}_verdict', report.get('summary', 'N/A'))}")
        parts.append(f"**Summary:** {report.get('summary', 'N/A')}")

        if report.get("key_findings"):
            parts.append("**Key Findings:**")
            for f in report["key_findings"]:
                parts.append(f"- {f}")

        if report.get("recommendations"):
            parts.append("**Recommendations:**")
            for rec in report["recommendations"]:
                parts.append(f"- {rec}")

        if report.get("risks"):
            parts.append("**Risks:**")
            for r in report["risks"]:
                parts.append(f"- {r}")

    parts.append(
        "\n## Your Review\n"
        "From your lens, answer: (1) Where do you agree? "
        "(2) Where do you conflict with their analysis? "
        "(3) What must change in their recommendations before you can align? "
        "Return as JSON with fields: agreements, conflicts, required_changes."
    )

    return "\n".join(parts)


# ----------------------------------------------------------------------
# Deliberation Modifiers
# ----------------------------------------------------------------------
# System-prompt fragments appended when agents enter board meeting mode.
# Persona is preserved — only the modality changes (now they see each other).
# ----------------------------------------------------------------------

DELIBERATION_MODIFIERS: Dict[str, str] = {
    "ceo": (
        "\n\n## BOARD MEETING MODE ACTIVE\n"
        "You are in an active board deliberation, not a solo analysis. "
        "If two executives disagree, name it explicitly. Direct your questions at named roles — "
        "do not ask the room. When you have enough, make a call. "
        "Unanimity is not the goal; clarity is."
    ),
    "cfo": (
        "\n\n## BOARD MEETING MODE ACTIVE\n"
        "Respond to challenges directly. Cite a number or state the assumption "
        "if you must estimate. If you change your position, say so explicitly and state why. "
        "Silence on a challenge reads as disagreement."
    ),
    "cto": (
        "\n\n## BOARD MEETING MODE ACTIVE\n"
        "State feasibility color: Green / Yellow / Red — do not qualify it with adjectives. "
        "Do not use 'complexity' as a shield; quantify it (eng-weeks, dollars, or both). "
        "If your initial assessment has shifted, say so explicitly."
    ),
    "cmo": (
        "\n\n## BOARD MEETING MODE ACTIVE\n"
        "Name the customer segment you are speaking about. "
        "Be specific about pricing impact — say by how much. "
        "If your position has evolved from earlier analysis, acknowledge what changed."
    ),
}


def build_deliberation_prompt(
    agent_name: str,
    round_num: int,
    core_prompt: str,
    prior_outputs: Dict[int, Dict[str, Any]] | None = None,
    challenges: Dict[str, list[str]] | None = None,
    board_context: bool = False,
) -> str:
    """Build a deliberative round prompt for a specific agent.

    Args:
        agent_name: Which agent to generate a prompt for.
        round_num: 1-5 (1=CEO frames, 2=CFO+CTO respond, 3=CMO respond,
                   4=All revise, 5=CEO synthesize)
        core_prompt: The original business decision.
        prior_outputs: Round-numbered dict of prior deliberation outputs.
                      Structure: {round_num: {"ceo": report, "cfo": report, ...}}
        challenges: Challenges directed at specific agents (e.g. "cfo" -> [list of questions]).
        board_context: If True, include the full board summary (used in round 5).

    Returns:
        Formatted prompt string for the LLM.
    """
    decision_type = _classify_decision(core_prompt)
    guidance = DECISION_TYPE_GUIDANCE.get(decision_type, DECISION_TYPE_GUIDANCE["generic"])

    def _format_report(name: str, r: Dict[str, Any]) -> List[str]:
        lines = []
        lines.append(f"### {name.upper()} Report")
        lines.append(f"**Title:** {r.get('title', 'N/A')}")
        # Verdict field differs by agent
        verdict_key = f"{name}_verdict" if name != "cmo" else "market_verdict"
        if name == "cto":
            verdict_key = "technical_verdict"
        verdict = r.get(verdict_key) or r.get("summary", "N/A")
        lines.append(f"**Verdict:** {verdict}")
        lines.append(f"**Summary:** {r.get('summary', 'N/A')}")
        if r.get("key_findings"):
            lines.append("**Key Findings:**")
            for f in r["key_findings"]:
                lines.append(f"- {f}")
        if r.get("recommendations"):
            lines.append("**Recommendations:**")
            for rec in r["recommendations"]:
                lines.append(f"- {rec}")
        if r.get("risks"):
            lines.append("**Risks:**")
            for risk in r["risks"]:
                lines.append(f"- {risk}")
        # Role-specific fields
        role_fields = r.get("role_specific", {})
        for k, v in role_fields.items():
            if v and k not in ("reasoning", "verdict"):
                lines.append(f"**{k}:** {v}")
        # Deliberation fields
        if r.get("agreements"):
            lines.append("**Agreements:**")
            for a in r["agreements"]:
                lines.append(f"- {a}")
        if r.get("conflicts"):
            lines.append("**Conflicts:**")
            for c in r["conflicts"]:
                lines.append(f"- {c}")
        if r.get("required_changes"):
            lines.append("**Required Changes:**")
            for ch in r["required_changes"]:
                lines.append(f"- {ch}")
        if r.get("revised_recommendations"):
            lines.append("**Revised Recommendations:**")
            for rev in r["revised_recommendations"]:
                lines.append(f"- {rev}")
        return lines

    # ------------------------------------------------------------------
    # ROUND 1 — CEO frames the board
    # ------------------------------------------------------------------
    if round_num == 1:
        parts = [
            f"## BOARD DELIBERATION — ROUND {round_num}",
            "You are the CEO. This board meeting is convened to address:",
            f"**{core_prompt}**",
            f"\nThe CFO, CTO, and CMO have each produced independent analyses. "
            f"Read across them and identify the three sharpest conflicts — "
            f"where two executives disagree on facts, priorities, or what to do.",
            "\nYour job is to frame the board, name the real disagreements, "
            "and direct specific questions to the CFO, CTO, and CMO that "
            "would cut through the most important conflict. "
            "Do not try to resolve here. Name and direct instead.",
            "\n**Prior Analyses:**",
        ]
        if prior_outputs:
            # First round — prior_outputs[0] contains the Phase-2 blind reports
            blind_reports = prior_outputs.get(0, {})
            for name in ["cfo", "cto", "cmo"]:
                report = blind_reports.get(name, {})
                if report:
                    parts.extend(_format_report(name, report))
                    parts.append("")
        parts.extend([
            "\n## Output Schema",
            "Return JSON with these fields:",
            "- **conflicts** (list[str]): Top 3 named conflicts. Format: '[Role A] vs [Role B]: [what they disagree on]'",
            "- **challenges_for_cfo** (list[str]): 1-2 pointed questions for the CFO. No softening.",
            "- **challenges_for_cto** (list[str]): 1-2 pointed questions for the CTO. No softening.",
            "- **challenges_for_cmo** (list[str]): 1-2 pointed questions for the CMO. No softening.",
            "- **summary** (str): One paragraph. The decision, the stakes, the three conflicts in one sentence each.",
            "Return JSON only. No markdown fences.",
        ])
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # ROUND 2 — CFO and CTO respond to CEO's challenges + cross-reference
    # ------------------------------------------------------------------
    elif round_num == 2:
        agent_challenges = challenges or {}
        my_questions = agent_challenges.get(agent_name, [])

        parts = [
            f"## BOARD DELIBERATION — ROUND {round_num}",
            f"You are the **{agent_name.upper()}**. CEO has framed the board. Here are your challenges:",
        ]
        if my_questions:
            for q in my_questions:
                parts.append(f"- {q}")
        else:
            parts.append("(No specific challenges from CEO directed at you this round.)")

        parts.extend([
            "\n**Context:** The other functional exec is also at the table. "
            "Read their report and identify where you agree, where you conflict, "
            "and what must change before you can support a board decision.",
            "\n**Other Executives' Reports:**",
        ])
        if prior_outputs:
            blind_reports = prior_outputs.get(0, {})
            cto_name = "cto" if agent_name == "cfo" else "cfo"
            other_report = blind_reports.get(cto_name, {})
            if other_report:
                parts.extend(_format_report(cto_name, other_report))
            # Also show CEO round-1 framing if available
            r1_outputs = prior_outputs.get(1, {})
            ceo_r1 = r1_outputs.get("ceo", {})
            if ceo_r1:
                parts.extend(_format_report("ceo", ceo_r1))

        # Schema based on agent role
        schema_notes = {
            "cfo": {
                "verdict_key": "financial_verdict",
                "additional": "- **capex_vs_opex** (str): State CapEx or OpEx. Why it matters here.\n"
                             "- **runway_impact_6mo** (str): Rough months of runway gained or lost.",
            },
            "cto": {
                "verdict_key": "technical_verdict",
                "additional": "- **build_cost_order_of_magnitude** (str): Eng-weeks or $ equivalent.\n"
                             "- **team_capacity_check** (str): Do we have the bandwidth?",
            },
        }
        role_info = schema_notes.get(agent_name, {})

        parts.extend([
            "\n## Output Schema",
            "Return JSON with these fields:",
            "- **agreements** (list[str]): Where you align with the other exec. Be specific.",
            "- **conflicts** (list[str]): Where you still disagree with the other exec's view.",
            "- **required_changes** (list[str]): What must change in the other exec's recommendations before you can align.",
            "- **summary** (str): One paragraph. Your position after hearing CEO framing and the other exec.",
            "- **round_number**: 2",
            f"- **{role_info.get('verdict_key', 'verdict')}** (str): Your updated verdict after this round.",
            role_info.get("additional", ""),
            "Return JSON only. No markdown fences.",
        ])
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # ROUND 3 — CMO responds to CEO + CFO/CTO framing, raises new challenges
    # ------------------------------------------------------------------
    elif round_num == 3:
        my_questions = (challenges or {}).get("cmo", [])

        parts = [
            "## BOARD DELIBERATION — ROUND 3",
            "You are the **CMO**. CEO has framed the board. CFO and CTO have responded. "
            "This is your turn to respond — and to raise challenges of your own.",
            "\n**CEO's questions directed at you:**",
        ]
        if my_questions:
            for q in my_questions:
                parts.append(f"- {q}")
        else:
            parts.append("(No specific challenges from CEO this round.)")

        parts.append("\n**All Prior Reports:**")
        if prior_outputs:
            blind_reports = prior_outputs.get(0, {})
            for name in ["cfo", "cto"]:
                r = blind_reports.get(name)
                if r:
                    parts.extend(_format_report(name, r))
                    parts.append("")
            r1 = prior_outputs.get(1, {}).get("ceo", {})
            if r1:
                parts.extend(_format_report("ceo", r1))
                parts.append("")
            r2 = prior_outputs.get(2, {})
            for name, r in r2.items():
                parts.extend(_format_report(name, r))
                parts.append("")

        parts.extend([
            "\n## Output Schema",
            "Return JSON with these fields:",
            "- **agreements** (list[str]): Where you align with CFO and/or CTO. Get specific.",
            "- **conflicts** (list[str]): Where you still disagree. Name the executive.",
            "- **required_changes** (list[str]): What must change in CFO's or CTO's recommendations.",
            "- **challenges_for_cfo** (list[str]): 1-2 questions for CFO that your customer data raises.",
            "- **challenges_for_cto** (list[str]): 1-2 questions for CTO about technical delivery risk.",
            "- **summary** (str): One paragraph.",
            "- **market_verdict** (str): Updated market verdict after this round.",
            "- **round_number**: 3",
            "Return JSON only. No markdown fences.",
        ])
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # ROUND 4 — All functional execs revise based on all prior challenges
    # ------------------------------------------------------------------
    elif round_num == 4:
        my_questions = (challenges or {}).get(agent_name, [])

        parts = [
            f"## BOARD DELIBERATION — ROUND {round_num}",
            f"You are the **{agent_name.upper()}**. This is your final revision round. "
            "You have been challenged by CEO and by your peer executives. "
            "Now confirm or update your position.",
            "\n**Questions and challenges directed at you:**",
        ]
        if my_questions:
            for q in my_questions:
                parts.append(f"- {q}")
        else:
            parts.append("(No external challenges directed at you this round — "
                         "proceed with self-revision if warranted.)")

        parts.append("\n**Full Deliberation History:**")
        if prior_outputs:
            for rnd in sorted(prior_outputs.keys()):
                if rnd == 0:
                    continue  # Skip blind reports in revision round
                parts.append(f"\n#### Round {rnd}:")
                for name, r in prior_outputs[rnd].items():
                    parts.extend(_format_report(name, r))
                    parts.append("")

        schema_for_agent = {
            "cfo": "- **revised_recommendations** (list[str]): Your updated recommendations after this round.\n"
                  "- **financial_verdict** (str): Final financial verdict.\n"
                  "- **revised_runway_impact** (str): Updated runway view.",
            "cto": "- **revised_recommendations** (list[str]): Your updated recommendations after this round.\n"
                  "- **technical_verdict** (str): Final feasibility verdict (Green/Yellow/Red).\n"
                  "- **revised_build_cost** (str): Updated build cost estimate.",
            "cmo": "- **revised_recommendations** (list[str]): Your updated recommendations after this round.\n"
                  "- **market_verdict** (str): Final market verdict.\n"
                  "- **revised_pricing_impact** (str): Updated pricing view.",
        }

        parts.extend([
            "\n## Output Schema",
            "Return JSON with these fields:",
            "- **challenged_by** (list[str]): List all executives who challenged you this round. "
             "Name them.",
            "- **revised_recommendations** (list[str]): Confirm or replace your prior recommendations. "
             "If unchanged, say 'Position confirmed — no changes required.'",
            "- **agreements** (list[str]): Final alignment points with other executives.",
            "- **conflicts** (list[str]): Residual conflicts that remain unresolved. "
             "Be honest — unresolved is fine.",
            "- **required_changes** (list[str]): Any prerequisite for your support of the final decision.",
            "- **summary** (str): Final paragraph. Position after full deliberation.",
            schema_for_agent.get(agent_name, ""),
            "- **round_number**: 4",
            "Return JSON only. No markdown fences.",
        ])
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # ROUND 5 — CEO synthesizes all rounds into board decision
    # ------------------------------------------------------------------
    elif round_num == 5:
        parts = [
            "## BOARD DELIBERATION — ROUND 5 (SYNTHESIS)",
            "You are the **CEO**. All rounds are complete. It is time to make the call.",
            f"\n**Decision:** {core_prompt}",
            "\n**Deliberation Summary** (synthesized — focus on agreements, conflicts, revised stances):",
        ]

        if prior_outputs:
            for rnd_num in sorted(prior_outputs.keys()):
                if rnd_num == 0:
                    continue  # Blind reports — skip
                rnd_data = prior_outputs[rnd_num]
                parts.append(f"\n[Round {rnd_num}]")
                # Extract only the fields we need (no verbose lists)
                for name, r in rnd_data.items():
                    summary = r.get("summary", "")[:300] if r.get("summary") else ""
                    verdicts = [
                        r.get(f"{name}_verdict"),
                        r.get("technical_verdict"),
                        r.get("market_verdict"),
                    ]
                    verdict = next((v for v in verdicts if v), "")
                    parts.append(f"  {name.upper()}: {verdict or summary}")
                    agreements = r.get("agreements", [])
                    if agreements:
                        parts.append(f"    Agrees: {' | '.join(str(a)[:80] for a in agreements[:3])}")
                    conflicts = r.get("conflicts", [])
                    if conflicts:
                        parts.append(f"    Conflicts: {' | '.join(str(c)[:80] for c in conflicts[:3])}")
                    revised = r.get("revised_recommendations", [])
                    if revised:
                        parts.append(f"    Revised: {' | '.join(str(x)[:80] for x in revised[:3])}")

        parts.extend([
            "\n## Output Schema",
            "Return JSON with a single **board_decision** key containing:",
            "- **consensus_points** (list[str]): Specific areas where all executives align.",
            "- **dissent_points** (list[str]): Areas where disagreement remains. Name which executives.",
            "- **final_priority_actions** (list[str]): 2-4 actions. Format: [Action] | Owner: [Role] | Timeframe: [When]",
            "- **dissenting_opinions** (list[str]): Any executive who still cannot support the decision.",
            "- **contingencies** (list[str]): If [condition], then [revisit or change action].",
            "- **summary** (str): One paragraph. The board's position in plain language.",
            "- **round_number**: 5",
            "Return JSON only. No markdown fences.",
        ])
        return "\n".join(parts)

    raise ValueError(f"Unknown deliberation round: {round_num}")