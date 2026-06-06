"""Shared pytest fixtures for all tests."""

import sys
from pathlib import Path

# Ensure src is on path for all tests
(sys.path.insert(0, str(Path(__file__).parent.parent)))

import pytest
from dataclasses import dataclass, field
from typing import Any


# -----------------------------------------------------------------------
# Minimal stubs — used across multiple test files to avoid importing
# code that requires network access / a running LLM.
# -----------------------------------------------------------------------

@dataclass
class FakeAgentReport:
    """Minimal AgentReport stand-in used for orchestrator state tests."""
    title: str = "Test Report"
    summary: str = "Test summary"
    key_findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    alignment_score: float = 0.5
    reasoning: dict[str, Any] = field(default_factory=dict)
    verdict: str | None = None
    contingencies: list[str] = field(default_factory=list)
    round_number: int = 0
    challenged_by: list[str] = field(default_factory=list)
    agreements: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    required_changes: list[str] = field(default_factory=list)
    revised_recommendations: list[str] = field(default_factory=list)
    challenges_for_cfo: list[str] = field(default_factory=list)
    challenges_for_cto: list[str] = field(default_factory=list)
    challenges_for_cmo: list[str] = field(default_factory=list)
    board_decision: dict[str, Any] | None = None
    capex_vs_opex: str | None = None
    runway_impact_6mo: str | None = None
    technical_verdict: str | None = None
    market_verdict: str | None = None

    def get_role_specific_fields(self) -> dict[str, Any]:
        """Return non-None role-specific fields."""
        d = {
            "verdict": self.verdict,
            "contingencies": self.contingencies,
            "capex_vs_opex": self.capex_vs_opex,
            "runway_impact_6mo": self.runway_impact_6mo,
            "technical_verdict": self.technical_verdict,
            "market_verdict": self.market_verdict,
            "round_number": self.round_number,
            "challenged_by": self.challenged_by,
            "agreements": self.agreements,
            "conflicts": self.conflicts,
            "required_changes": self.required_changes,
            "revised_recommendations": self.revised_recommendations,
            "challenges_for_cfo": self.challenges_for_cfo,
            "challenges_for_cto": self.challenges_for_cto,
            "challenges_for_cmo": self.challenges_for_cmo,
            "board_decision": self.board_decision,
        }
        return {k: v for k, v in d.items() if v is not None and v != []}


# -----------------------------------------------------------------------
# Common fixtures for all tests
# -----------------------------------------------------------------------

@pytest.fixture
def project_root():
    """Get project root path."""
    return Path(__file__).parent.parent


# -----------------------------------------------------------------------
# Minimal SimulationState (mirrors orchestrator.py's definition)
# -----------------------------------------------------------------------

@dataclass
class FakeSimulationState:
    core_prompt: str
    simulation_id: str = "test-simulation-001"
    data_corpus: dict[str, str] = field(default_factory=dict)
    decision_point: str | None = None
    status: str = "idle"
    phase: str = ""
    agent_outputs: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    deliberation_round: int = 0
    challenges: dict[str, list[str]] = field(default_factory=dict)
    deliberation_outputs: dict[int, dict[str, Any]] = field(default_factory=dict)


# -----------------------------------------------------------------------
# Shared fixtures
# -----------------------------------------------------------------------

@pytest.fixture
def sample_agent_response() -> dict[str, Any]:
    """A complete, valid LLM response for the CEO agent."""
    return {
        "title": "Infrastructure Investment Strategy",
        "strategic_verdict": "Buy core infrastructure to build a durable moat.",
        "summary": "We must choose between buying and leasing equipment. "
                   "Buying builds equity and control; leasing preserves cash. "
                   "We recommend a hybrid approach.",
        "key_findings": [
            "Equipment represents 40% of our current operating cost base.",
            "Leasing contracts include unfavorable exit clauses.",
        ],
        "recommendations": [
            "Buy core compute infrastructure | Owner: CTO | Timeframe: Q2",
            "Lease burst capacity | Owner: CFO | Timeframe: Immediate",
        ],
        "risks": [
            "Buying ties up capital needed for hiring. "
            "Consequence: Slower growth velocity. Mitigation: CFO to model the trade-off.",
        ],
        "what_i_need_from_cfo": "Tell me the exact runway impact of buying $500k in equipment.",
        "what_i_need_from_cto": "Give me the Green/Yellow/Red on buying in-house.",
        "what_i_need_from_cmo": "Will leasing signal weakness to institutional clients?",
        "alignment_score": 0.78,
        "reasoning": [
            "Step 1: equipment is our biggest cost driver at 40%.",
            "Step 2: leasing locks us into a 3-year contract with penalty exit.",
            "Step 3: buying preserves long-term control at the cost of upfront capital.",
        ],
        "contingencies": [
            "If runway drops below 9 months, defer the buy decision to after Series A.",
        ],
    }


@pytest.fixture
def sample_cfo_response() -> dict[str, Any]:
    """A complete, valid LLM response for the CFO agent."""
    return {
        "title": "Buy vs Lease Financial Analysis",
        "financial_verdict": "Leasing preserves runway. Buying increases long-term total cost of ownership.",
        "summary": "Leasing costs $120k/year with no upfront capital. Buying costs $500k upfront but "
                   "eliminates $240k in cumulative lease payments over 5 years.",
        "key_findings": [
            "Lease: $120k/year, no upfront, 3-year minimum commitment.",
            "Buy: $500k upfront, but eliminates $240k cumulative lease cost over 5 years.",
        ],
        "recommendations": [
            "Lease burst capacity now | Impact: -$10k/month runway | Owner: CFO",
            "Build buy model if CTO confirms Green feasibility | Owner: CFO | Timeframe: 2 weeks",
        ],
        "risks": [
            "Underestimating TCO: lease payments may exceed purchase over 3-5 years. "
            "[Probability: High]",
        ],
        "capex_vs_opex": "Lease = OpEx, fully expensed. Buy = CapEx, depreciated over 5 years.",
        "runway_impact_6mo": "Buying: -$500k immediate. Leasing: -$60k/month ongoing.",
        "series_a_signal": "Negative — buying signals confidence but ties cash that investors expect deployed.",
        "financial_reserves_needed": "$75k minimum cash reserve after any infrastructure purchase.",
        "alignment_score": 0.65,
        "reasoning": ["Lease vs buy is not binary — hybrid approach optimal."],
        "contingencies": ["If runway < 12 months, only lease."],
    }


@pytest.fixture
def sample_cto_response() -> dict[str, Any]:
    """A complete, valid LLM response for the CTO agent."""
    return {
        "title": "Buy vs Lease Infrastructure Feasibility",
        "technical_verdict": "Green — buying in-house is feasible with a 12-week implementation.",
        "summary": "In-house infrastructure is feasible in 12 weeks. It gives us the maximum "
                   "control over the technical moat. Leasing introduces vendor lock-in risk.",
        "key_findings": [
            "In-house GPU cluster requires 12 weeks to provision and configure.",
            "Leasing AWS/GCP creates lock-in: 6-month notice period, egress costs are prohibitive.",
        ],
        "recommendations": [
            "Buy GPU cluster in-house | Complexity: Medium | Lead: CTO | Est: 12 weeks",
        ],
        "risks": ["Hardware becomes obsolete within 3 years. [probability: Med]"],
        "build_cost_order_of_magnitude": "Roughly 8 eng-weeks + $500k hardware.",
        "moat_impact": "Creates (+) — full control over the infrastructure stack.",
        "team_capacity_check": "Yes, with 2 senior engineers allocated full-time.",
        "vendor_lockin_risk": "High (leasing) vs Low (buying). Exit trigger: 6-month notice + $150k egress.",
        "alignment_score": 0.82,
        "reasoning": ["Green — no major restructure required."],
        "contingencies": ["If lead time > 8 weeks, lease as interim."],
    }


@pytest.fixture
def sample_cmo_response() -> dict[str, Any]:
    """A complete, valid LLM response for the CMO agent."""
    return {
        "title": "Infrastructure Signal to the Market",
        "market_verdict": "Buying signals strength to enterprise clients; leasing signals caution.",
        "summary": "Institutional clients (banks, hedge funds) interpret in-house infrastructure "
                   "as a sign of commitment to reliability. Leasing sends a cautious signal.",
        "key_findings": [
            "85% of enterprise prospects ask about infrastructure ownership in procurement.",
            "SLA: buying provides 99.9% guaranteed vs 99.5% for shared leased infrastructure.",
        ],
        "recommendations": [
            "Lead GTM with infrastructure ownership story | Segment: Banks/HedgeFunds | Owner: CMO",
        ],
        "risks": [
            "If infrastructure fails publicly under self-managed stack, brand impact is severe. "
            "[probability: Low]",
        ],
        "pricing_impact": "Yes. Buying supports premium pricing (+15-20%) for enterprise SLA tiers.",
        "competitive_signal": "Signals long-term commitment. Competitors using managed cloud appear reactive.",
        "customer_segment_view": (
            "Banks: Helps — ownership underpins the reliability narrative. "
            "Hedge Funds: Helps — SLA commitment is a procurement requirement."
        ),
        "go_to_market_implication": (
            "Change sales pitch to lead with infrastructure commitment. "
            "Shifts demo focus to self-hosted vs managed."
        ),
        "alignment_score": 0.73,
        "reasoning": ["Market signals strongly support buying."],
        "contingencies": [
            "If buying delays product launch by > 4 weeks, re-evaluate.",
        ],
    }


@pytest.fixture
def simulation_state() -> FakeSimulationState:
    """A populated SimulationState for orchestrator tests."""
    return FakeSimulationState(
        core_prompt="Buy vs lease equipment?",
        data_corpus={"company_background.md": "#Acme Corp\nAn enterprise SaaS company."},
        decision_point="Decision required for: Buy vs lease equipment?",
        status="initialized",
    )


@pytest.fixture
def simulation_state_with_reports(
    simulation_state,
    sample_agent_response,
    sample_cfo_response,
    sample_cto_response,
    sample_cmo_response,
) -> FakeSimulationState:
    """SimulationState with Phase-2 agent reports already populated."""
    from src.agents.interface import AgentReport

    reports = {
        "ceo": AgentReport.from_llm_response("ceo", sample_agent_response),
        "cfo": AgentReport.from_llm_response("cfo", sample_cfo_response),
        "cto": AgentReport.from_llm_response("cto", sample_cto_response),
        "cmo": AgentReport.from_llm_response("cmo", sample_cmo_response),
    }
    state = simulation_state
    state.agent_outputs = reports
    state.status = "analyzing"
    return state