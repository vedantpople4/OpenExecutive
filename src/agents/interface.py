from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentReport:
    """Standard report format for agent insights."""

    title: str
    summary: str = ""
    key_findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    alignment_score: float = 0.5  # renamed from confidence_score for honesty
    reasoning: dict[str, Any] = field(default_factory=dict)

    # Role-specific fields (populated when present in LLM response)
    verdict: Optional[str] = None       # CEO: strategic | CFO: financial | CTO: technical | CMO: market
    contingencies: list[str] = field(default_factory=list)  # all agents

    # CFO-specific
    capex_vs_opex: Optional[str] = None
    runway_impact_6mo: Optional[str] = None
    series_a_signal: Optional[str] = None
    financial_reserves_needed: Optional[str] = None

    # CTO-specific
    technical_verdict: Optional[str] = None  # Green/Yellow/Red
    build_cost_order_of_magnitude: Optional[str] = None
    moat_impact: Optional[str] = None
    team_capacity_check: Optional[str] = None
    vendor_lockin_risk: Optional[str] = None

    # CMO-specific
    market_verdict: Optional[str] = None
    pricing_impact: Optional[str] = None
    competitive_signal: Optional[str] = None
    customer_segment_view: Optional[str] = None
    go_to_market_implication: Optional[str] = None

    # CEO-specific cross-agent asks
    what_i_need_from_cfo: Optional[str] = None
    what_i_need_from_cto: Optional[str] = None
    what_i_need_from_cmo: Optional[str] = None

    # ----- Deliberation fields (all agents) -----
    agreements: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    required_changes: list[str] = field(default_factory=list)
    revised_recommendations: list[str] = field(default_factory=list)
    round_number: int = 0
    challenged_by: list[str] = field(default_factory=list)

    # CEO-only: round-1 framing — challenges directed at other execs
    challenges_for_cfo: list[str] = field(default_factory=list)
    challenges_for_cto: list[str] = field(default_factory=list)
    challenges_for_cmo: list[str] = field(default_factory=list)

    # CEO-only: round-5 synthesis output
    board_decision: Optional[dict[str, Any]] = None

    @classmethod
    def from_llm_response(cls, agent_name: str, response: dict[str, Any]) -> "AgentReport":
        """Construct AgentReport from LLM JSON response, mapping role-specific fields.

        Args:
            agent_name: One of ceo, cfo, cto, cmo
            response: Parsed JSON from LLM

        Returns:
            AgentReport instance
        """
        verdict_map = {
            "ceo": response.get("strategic_verdict"),
            "cfo": response.get("financial_verdict"),
            "cto": response.get("technical_verdict"),
            "cmo": response.get("market_verdict"),
        }

        # reasoning can come back as a list (per prompt spec) or dict
        # normalize to dict for compatibility across the codebase
        raw_reasoning = response.get("reasoning", {})
        if isinstance(raw_reasoning, list):
            reasoning = {"chains": raw_reasoning}
        elif isinstance(raw_reasoning, dict):
            reasoning = raw_reasoning
        else:
            reasoning = {}

        return cls(
            title=response.get("title", "Untitled Report"),
            summary=response.get("summary", ""),
            key_findings=response.get("key_findings", []),
            recommendations=response.get("recommendations", []),
            risks=response.get("risks", []),
            alignment_score=float(response.get("alignment_score", 0.5)),
            reasoning=reasoning,
            verdict=verdict_map.get(agent_name),
            contingencies=response.get("contingencies", []),

            # CFO
            capex_vs_opex=response.get("capex_vs_opex"),
            runway_impact_6mo=response.get("runway_impact_6mo"),
            series_a_signal=response.get("series_a_signal"),
            financial_reserves_needed=response.get("financial_reserves_needed"),

            # CTO
            technical_verdict=response.get("technical_verdict"),
            build_cost_order_of_magnitude=response.get("build_cost_order_of_magnitude"),
            moat_impact=response.get("moat_impact"),
            team_capacity_check=response.get("team_capacity_check"),
            vendor_lockin_risk=response.get("vendor_lockin_risk"),

            # CMO
            market_verdict=response.get("market_verdict"),
            pricing_impact=response.get("pricing_impact"),
            competitive_signal=response.get("competitive_signal"),
            customer_segment_view=response.get("customer_segment_view"),
            go_to_market_implication=response.get("go_to_market_implication"),

            # CEO
            what_i_need_from_cfo=response.get("what_i_need_from_cfo"),
            what_i_need_from_cto=response.get("what_i_need_from_cto"),
            what_i_need_from_cmo=response.get("what_i_need_from_cmo"),

            # Deliberation (all agents)
            agreements=response.get("agreements", []),
            conflicts=response.get("conflicts", []),
            required_changes=response.get("required_changes", []),
            revised_recommendations=response.get("revised_recommendations", []),
            round_number=int(response.get("round_number", 0)),
            challenged_by=response.get("challenged_by", []),

            # CEO deliberations
            challenges_for_cfo=response.get("challenges_for_cfo", []),
            challenges_for_cto=response.get("challenges_for_cto", []),
            challenges_for_cmo=response.get("challenges_for_cmo", []),
            board_decision=response.get("board_decision"),
        )

    def get_role_specific_fields(self) -> dict[str, Any]:
        """Return non-None role-specific fields as a dict. Useful for synthesis.

        Returns:
            Dict of {field_name: value} excluding None values.
        """
        role_fields = {
            "verdict": self.verdict,
            "contingencies": self.contingencies,
            "capex_vs_opex": self.capex_vs_opex,
            "runway_impact_6mo": self.runway_impact_6mo,
            "series_a_signal": self.series_a_signal,
            "financial_reserves_needed": self.financial_reserves_needed,
            "technical_verdict": self.technical_verdict,
            "build_cost_order_of_magnitude": self.build_cost_order_of_magnitude,
            "moat_impact": self.moat_impact,
            "team_capacity_check": self.team_capacity_check,
            "vendor_lockin_risk": self.vendor_lockin_risk,
            "market_verdict": self.market_verdict,
            "pricing_impact": self.pricing_impact,
            "competitive_signal": self.competitive_signal,
            "customer_segment_view": self.customer_segment_view,
            "go_to_market_implication": self.go_to_market_implication,
            "what_i_need_from_cfo": self.what_i_need_from_cfo,
            "what_i_need_from_cto": self.what_i_need_from_cto,
            "what_i_need_from_cmo": self.what_i_need_from_cmo,
            # Deliberation
            "agreements": self.agreements,
            "conflicts": self.conflicts,
            "required_changes": self.required_changes,
            "revised_recommendations": self.revised_recommendations,
            "round_number": self.round_number,
            "challenged_by": self.challenged_by,
            "challenges_for_cfo": self.challenges_for_cfo,
            "challenges_for_cto": self.challenges_for_cto,
            "challenges_for_cmo": self.challenges_for_cmo,
            "board_decision": self.board_decision,
        }
        return {k: v for k, v in role_fields.items() if v is not None and v != []}