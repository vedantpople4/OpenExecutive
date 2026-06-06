"""Tests for openexec/agents/interface.py — AgentReport."""

import pytest
from openexec.agents.interface import AgentReport


class TestAgentReportFromLLMResponse:
    """AgentReport.from_llm_response() — factory from LLM JSON output."""

    def test_complete_response_maps_all_fields(self, sample_agent_response):
        report = AgentReport.from_llm_response("ceo", sample_agent_response)

        assert report.title == "Infrastructure Investment Strategy"
        assert report.summary == sample_agent_response["summary"]
        assert report.key_findings == sample_agent_response["key_findings"]
        assert report.recommendations == sample_agent_response["recommendations"]
        assert report.alignment_score == 0.78
        assert report.verdict == "Buy core infrastructure to build a durable moat."
        assert "buying" in report.what_i_need_from_cto.lower()

    def test_response_type_routing_for_ceo(self, sample_agent_response):
        """CEO verdict maps from 'strategic_verdict'."""
        report = AgentReport.from_llm_response("ceo", sample_agent_response)
        assert report.verdict == sample_agent_response["strategic_verdict"]
        # strategic_verdict is not a field on AgentReport, it's read from response
        assert report.title == "Infrastructure Investment Strategy"
        assert report.summary == sample_agent_response["summary"]

    def test_response_type_routing_for_cfo(self, sample_cfo_response):
        """CFO verdict maps from 'financial_verdict', CFO fields populated."""
        report = AgentReport.from_llm_response("cfo", sample_cfo_response)
        assert report.verdict == sample_cfo_response["financial_verdict"]
        assert report.capex_vs_opex == "Lease = OpEx, fully expensed. Buy = CapEx, depreciated over 5 years."
        assert report.runway_impact_6mo == "Buying: -$500k immediate. Leasing: -$60k/month ongoing."
        assert report.series_a_signal == sample_cfo_response["series_a_signal"]

    def test_response_type_routing_for_cto(self, sample_cto_response):
        """CTO verdict maps from 'technical_verdict'; CTO-specific fields populated."""
        report = AgentReport.from_llm_response("cto", sample_cto_response)
        assert report.technical_verdict == sample_cto_response["technical_verdict"]
        assert report.build_cost_order_of_magnitude == "Roughly 8 eng-weeks + $500k hardware."
        assert report.moat_impact == "Creates (+) — full control over the infrastructure stack."
        assert report.vendor_lockin_risk == "High (leasing) vs Low (buying). Exit trigger: 6-month notice + $150k egress."
        assert report.team_capacity_check == "Yes, with 2 senior engineers allocated full-time."

    def test_response_type_routing_for_cmo(self, sample_cmo_response):
        """CMO verdict maps from 'market_verdict'; CMO-specific fields populated."""
        report = AgentReport.from_llm_response("cmo", sample_cmo_response)
        assert report.market_verdict == sample_cmo_response["market_verdict"]
        assert report.pricing_impact == sample_cmo_response["pricing_impact"]
        assert report.competitive_signal == sample_cmo_response["competitive_signal"]
        assert "Banks: Helps" in report.customer_segment_view
        assert report.go_to_market_implication and len(report.go_to_market_implication) > 10

    def test_reasoning_as_list_is_normalized_to_dict(self):
        """reasoning: [a, b] arrays are normalised to {chains: [a, b]}."""
        raw = {
            "title": "T", "summary": "S",
            "reasoning": ["chain step 1", "chain step 2"],
        }
        report = AgentReport.from_llm_response("ceo", raw)
        assert isinstance(report.reasoning, dict)
        assert report.reasoning["chains"] == ["chain step 1", "chain step 2"]

    def test_reasoning_as_dict_passes_through(self):
        """reasoning: {key: value} dicts pass through unchanged."""
        raw = {
            "title": "T", "summary": "S",
            "reasoning": {"context_used": ["doc1"], "confidence_note": "thin data"},
        }
        report = AgentReport.from_llm_response("cto", raw)
        assert report.reasoning == {"context_used": ["doc1"], "confidence_note": "thin data"}

    def test_reasoning_null_becomes_empty_dict(self):
        raw = {"title": "T", "summary": "S", "reasoning": None}
        report = AgentReport.from_llm_response("cmo", raw)
        assert report.reasoning == {}

    def test_missing_optional_fields_default_correctly(self):
        """Fields not present in response should get sensible defaults."""
        raw = {"title": "Minimal", "summary": "Just title and summary."}
        report = AgentReport.from_llm_response("cfo", raw)

        assert report.title == "Minimal"
        assert report.summary == "Just title and summary."
        assert report.key_findings == []
        assert report.recommendations == []
        assert report.risks == []
        assert report.alignment_score == 0.5  # default
        assert report.contingencies == []

    def test_alignment_score_is_float(self):
        """alignment_score must be a Python float even when returned as int."""
        raw = {"title": "T", "summary": "S", "alignment_score": 1}
        report = AgentReport.from_llm_response("cmo", raw)
        assert isinstance(report.alignment_score, float)
        assert report.alignment_score == 1.0

    def test_deliberation_fields_populated(self):
        """Deliberation-round fields are parsed from LLM response."""
        raw = {
            "title": "Deliberation Round 4",
            "summary": "CFO revising position.",
            "round_number": 4,
            "agreements": ["TCO model needed"],
            "conflicts": ["CFO vs CTO on timeline"],
            "required_changes": ["CTO must deliver engineering estimate"],
            "revised_recommendations": ["Hybrid: buy core, lease burst"],
            "challenged_by": ["ceo", "cmo"],
            "challenges_for_cfo": [],
            "challenges_for_cto": [],
            "challenges_for_cmo": [],
        }
        report = AgentReport.from_llm_response("cfo", raw)
        assert report.round_number == 4
        assert report.agreements == ["TCO model needed"]
        assert report.conflicts == ["CFO vs CTO on timeline"]
        assert report.required_changes == ["CTO must deliver engineering estimate"]
        assert report.revised_recommendations == ["Hybrid: buy core, lease burst"]
        assert report.challenged_by == ["ceo", "cmo"]

    def test_board_decision_ceo_only(self):
        """board_decision is populated for CEO round-5 synthesis."""
        raw = {
            "title": "CEO Synthesis",
            "summary": "Board decision pending.",
            "round_number": 5,
            "board_decision": {
                "consensus_points": ["TCO analysis required"],
                "dissent_points": [],
                "final_priority_actions": [
                    "CTO delivers TCO model | Owner: CTO | Timeframe: 2 Weeks",
                ],
                "dissenting_opinions": [],
                "contingencies": ["If runway < 9mo, defer all capex."],
                "summary": "Pause and quantify before deciding.",
            },
        }
        report = AgentReport.from_llm_response("ceo", raw)
        assert report.board_decision is not None
        assert "TCO analysis required" in report.board_decision["consensus_points"]
        assert report.board_decision["final_priority_actions"][0].startswith("CTO delivers")


class TestAgentReportGetRoleSpecificFields:
    """AgentReport.get_role_specific_fields()."""

    def test_excludes_none_and_empty_values(self):
        """Fields that are None or [] should not appear in output dict."""
        report = AgentReport(
            title="T", summary="S",
            alignment_score=0.7,
            technical_verdict="Green",
            market_verdict=None,  # should be excluded
            risks=[],  # empty list should be excluded
        )
        fields = report.get_role_specific_fields()
        assert "technical_verdict" in fields
        assert "market_verdict" not in fields  # None → excluded
        assert "risks" not in fields  # [] → excluded

    def test_includes_all_populated_role_fields(self, sample_cto_response):
        report = AgentReport.from_llm_response("cto", sample_cto_response)
        fields = report.get_role_specific_fields()

        assert "technical_verdict" in fields
        assert fields["technical_verdict"] == "Green — buying in-house is feasible with a 12-week implementation."
        assert "build_cost_order_of_magnitude" in fields
        assert "moat_impact" in fields
        assert "team_capacity_check" in fields
        assert "vendor_lockin_risk" in fields

    def test_includes_deliberation_fields_when_populated(self):
        report = AgentReport(
            title="T", summary="S",
            round_number=4,
            agreements=["A1", "A2"],
            conflicts=["C1"],
            revised_recommendations=["R1"],
            challenged_by=["ceo"],
        )
        fields = report.get_role_specific_fields()
        assert fields["agreements"] == ["A1", "A2"]
        assert fields["conflicts"] == ["C1"]
        assert fields["revised_recommendations"] == ["R1"]
        assert fields["challenged_by"] == ["ceo"]

    def test_board_decision_included_when_present(self, sample_agent_response):
        board_decision = {
            "consensus_points": ["Test"],
            "dissent_points": [],
            "final_priority_actions": ["Act 1"],
            "dissenting_opinions": [],
            "contingencies": [],
            "summary": "Test.",
        }
        # Directly set board_decision (from_llm_response would normally do this)
        raw = {**sample_agent_response, "board_decision": board_decision, "round_number": 5}
        report = AgentReport.from_llm_response("ceo", raw)
        fields = report.get_role_specific_fields()
        assert "board_decision" in fields
        assert fields["board_decision"]["consensus_points"] == ["Test"]


class TestAgentReportDataclassIntegrity:
    """Basic dataclass creation and immutability."""

    def test_can_construct_minimal_report(self):
        report = AgentReport(title="Test", summary="Summary")
        assert report.title == "Test"
        assert report.alignment_score == 0.5  # default

    def test_all_deliberation_fields_present(self):
        """Ensure all deliberation fields are on the dataclass definition."""
        report = AgentReport(
            title="T", summary="S",
            round_number=4,
            agreements=["agree"],
            conflicts=["disagree"],
            required_changes=["change"],
            revised_recommendations=["revised"],
            challenged_by=["ceo"],
            challenges_for_cfo=["Q1"],
            challenges_for_cto=["Q2"],
            board_decision={"summary": "Done"},
        )
        assert report.round_number == 4
        assert len(report.agreements) == 1
        assert len(report.conflicts) == 1

    def test_role_specific_fields_have_correct_types(self):
        """Role-specific fields should be Optional or list, never wrong type."""
        report = AgentReport(
            title="T", summary="S",
            capex_vs_opex="OpEx",
            runway_impact_6mo="-6 months",
            technical_verdict="Yellow",
            market_verdict="Wins",
            alignment_score=0.91,
        )
        assert isinstance(report.capex_vs_opex, str)
        assert isinstance(report.technical_verdict, str)