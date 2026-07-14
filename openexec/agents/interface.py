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

    # Role-specific and deliberation fields
    verdict: Optional[str] = None       # CEO: strategic | financial | technical | market
    contingencies: list[str] = field(default_factory=list)
    extra_fields: dict[str, Any] = field(default_factory=dict)

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

    # True when the LLM call failed and this report is a hardcoded placeholder,
    # not real analysis. Must stay visible downstream so a stub is never
    # mistaken for a genuine agent position.
    is_fallback: bool = False

    @classmethod
    def from_llm_response(cls, agent_name: str, response: dict[str, Any]) -> "AgentReport":
        """Construct AgentReport from LLM JSON response, mapping role-specific fields."""
        verdict_map = {
            "ceo": response.get("strategic_verdict"),
            "cfo": response.get("financial_verdict"),
            "cto": response.get("technical_verdict"),
            "cmo": response.get("market_verdict"),
        }

        raw_reasoning = response.get("reasoning", {})
        reasoning = {"chains": raw_reasoning} if isinstance(raw_reasoning, list) else (raw_reasoning if isinstance(raw_reasoning, dict) else {})

        standard_fields = {
            "title", "summary", "key_findings", "recommendations", "risks",
            "alignment_score", "reasoning", "contingencies", "agreements",
            "conflicts", "required_changes", "revised_recommendations",
            "round_number", "challenged_by", "challenges_for_cfo",
            "challenges_for_cto", "challenges_for_cmo", "board_decision"
        }

        extra_fields = {k: v for k, v in response.items() if k not in standard_fields and k not in ["strategic_verdict", "financial_verdict", "technical_verdict", "market_verdict"]}

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
            extra_fields=extra_fields,
            agreements=response.get("agreements", []),
            conflicts=response.get("conflicts", []),
            required_changes=response.get("required_changes", []),
            revised_recommendations=response.get("revised_recommendations", []),
            round_number=int(response.get("round_number", 0)),
            challenged_by=response.get("challenged_by", []),
            challenges_for_cfo=response.get("challenges_for_cfo", []),
            challenges_for_cto=response.get("challenges_for_cto", []),
            challenges_for_cmo=response.get("challenges_for_cmo", []),
            board_decision=response.get("board_decision"),
        )

    def get_role_specific_fields(self) -> dict[str, Any]:
        """Return non-None role-specific fields as a dict. Useful for synthesis."""
        role_fields = {
            "verdict": self.verdict,
            "contingencies": self.contingencies,
            **self.extra_fields,
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

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict representation."""
        return {
            "title": self.title,
            "summary": self.summary,
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "risks": self.risks,
            "alignment_score": self.alignment_score,
            "round_number": self.round_number,
            "is_fallback": self.is_fallback,
            **self.get_role_specific_fields(),
        }