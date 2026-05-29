"""Tests for src/ai/prompts.py — prompt builders and routing."""

import pytest
from src.ai.prompts import (
    AGENT_SYSTEM_PROMPTS,
    DELIBERATION_MODIFIERS,
    DECISION_TYPE_GUIDANCE,
    get_agent_system_prompt,
    build_analysis_prompt,
    build_deliberation_prompt,
    build_review_prompt,
    _classify_decision,
)


# -----------------------------------------------------------------------
# _classify_decision
# -----------------------------------------------------------------------

class TestClassifyDecision:
    """Decision type routing."""

    @pytest.mark.parametrize("prompt,expected", [
        ("buy new servers", "infrastructure"),
        ("lease GPU cluster", "infrastructure"),
        ("build data center", "infrastructure"),
        ("set pricing for enterprise", "pricing"),
        ("should we charge more for premium?", "pricing"),
        ("hire 5 engineers", "hiring"),
        ("Should we expand the team?", "hiring"),
        ("expand to European market", "market"),
        ("launch in Asia", "market"),
        ("should we raise Series A now?", "funding"),
        ("how to allocate $2M capital", "funding"),
        ("build a mobile app", "product"),
        ("ship a new feature", "product"),
        ("what to do about strategy?", "generic"),
        ("should we pivot?", "generic"),
    ])
    def test_classification_returns_correct_type(self, prompt, expected):
        assert _classify_decision(prompt) == expected

    def test_case_insensitive(self):
        assert _classify_decision("BUY NEW SERVERS") == "infrastructure"
        assert _classify_decision("Lease GPUs") == "infrastructure"


# -----------------------------------------------------------------------
# get_agent_system_prompt
# -----------------------------------------------------------------------

class TestGetAgentSystemPrompt:
    def test_all_four_agents_have_prompts(self):
        for name in ("ceo", "cfo", "cto", "cmo"):
            prompt = get_agent_system_prompt(name)
            assert isinstance(prompt, str)
            assert len(prompt) > 50
            assert "JSON" in prompt  # all prompts mention the JSON output requirement

    def test_raises_on_unknown_agent(self):
        with pytest.raises(ValueError, match="Unknown agent"):
            get_agent_system_prompt("coo")

    def test_ceo_prompt_mentions_strategic_lens(self):
        prompt = get_agent_system_prompt("ceo")
        assert "WHY" in prompt or "Why" in prompt

    def test_cfo_prompt_mentions_financial_lens(self):
        prompt = get_agent_system_prompt("cfo")
        assert "runway" in prompt.lower() or "cost" in prompt.lower()

    def test_cto_prompt_mentions_feasibility_color(self):
        prompt = get_agent_system_prompt("cto")
        # CTO should have Green/Yellow/Red language
        assert "Green" in prompt or "feasibility" in prompt.lower()

    def test_cmo_prompt_mentions_customer_segments(self):
        prompt = get_agent_system_prompt("cmo")
        assert "customer" in prompt.lower() or "segment" in prompt.lower()


# -----------------------------------------------------------------------
# build_analysis_prompt
# -----------------------------------------------------------------------

class TestBuildAnalysisPrompt:
    def test_routes_infrastructure_decision(self):
        prompt = build_analysis_prompt("Buy new servers?", agent_name="cto")
        assert "infrastructure" in prompt.lower() or "INFRASTRUCTURE" in prompt

    def test_routes_pricing_decision(self):
        prompt = build_analysis_prompt("Should we increase prices?", agent_name="cfo")
        assert "pricing" in prompt.lower()

    def test_core_prompt_appears_in_output(self):
        core = "Should we lease or buy equipment?"
        prompt = build_analysis_prompt(core, agent_name="ceo")
        assert core in prompt

    def test_data_corpus_injected(self):
        corpus = {"market_data.md": "Enterprise market is $5B TAM."}
        prompt = build_analysis_prompt("Enter enterprise?", agent_name="cmo", data_corpus=corpus)
        assert "market_data.md" in prompt
        assert "Enterprise market is $5B TAM." in prompt

    def test_data_corpus_truncated_at_2500_chars(self):
        long_content = "x" * 3000
        corpus = {"long_doc.md": long_content}
        prompt = build_analysis_prompt("Analyze this.", agent_name="ceo", data_corpus=corpus)
        # The content should have been truncated
        assert len(prompt) < len(long_content) + 500
        assert "..." in prompt  # truncation marker

    def test_memory_context_not_repeated(self):
        """memory_context.md should be skipped from data_corpus injection."""
        corpus = {"memory_context.md": "Should not appear.", "other.md": "Should appear."}
        prompt = build_analysis_prompt("Test decision", agent_name="cmo", data_corpus=corpus)
        assert "memory_context.md" not in prompt
        assert "other.md" in prompt

    def test_returns_string(self):
        result = build_analysis_prompt("Should we pivot?", agent_name="ceo")
        assert isinstance(result, str)
        assert len(result) > 20


# -----------------------------------------------------------------------
# build_review_prompt
# -----------------------------------------------------------------------

class TestBuildReviewPrompt:
    def test_includes_other_report_titles(self):
        other_reports = {
            "cto": {
                "title": "CTO Feasibility Report",
                "summary": "Buy is feasible in 12 weeks.",
                "key_findings": ["Finding A"],
                "recommendations": ["Recommendation A"],
                "risks": ["Risk A"],
                "technical_verdict": "Green",
            },
        }
        prompt = build_review_prompt("cfo", other_reports)
        assert "CTO Feasibility Report" in prompt
        assert "Green" in prompt

    def test_excludes_self_from_review(self):
        """Agent reviewing itself should not appear in the prompt."""
        prompt = build_review_prompt("cfo", {
            "cfo": {"title": "CFO Financial Report"},
            "cto": {"title": "CTO Technical Report"},
        })
        assert "CFO Financial Report" not in prompt
        assert "CTO Technical Report" in prompt

    def test_output_schema_mentions_agreements_conflicts_required_changes(self):
        prompt = build_review_prompt("cmo", {
            "cfo": {"title": "T", "summary": "S"},
        })
        assert "agreements" in prompt.lower()
        assert "conflicts" in prompt.lower()
        assert "required_changes" in prompt.lower()


# -----------------------------------------------------------------------
# build_deliberation_prompt
# -----------------------------------------------------------------------

class TestBuildDeliberationPrompt:
    """build_deliberation_prompt() — round-specific deliberation prompts."""

    def test_round_1_is_ceo_only(self):
        prompt = build_deliberation_prompt("ceo", 1, "Buy vs lease?", {}, {})
        assert "ROUND 1" in prompt
        assert "CEO" in prompt
        assert "challenges_for_cfo" in prompt.lower()
        assert "conflicts" in prompt.lower()

    def test_round_2_includes_ceo_challenges(self):
        challenges = {"cfo": ["Why does CFO prefer leasing?", "What is the TCO for buying?"]}
        prompt = build_deliberation_prompt("cfo", 2, "Test", {}, challenges)
        assert "Why does CFO prefer leasing?" in prompt

    def test_round_2_cto_responds(self):
        prior_outputs = {
            0: {"cfo": {"summary": "CFO summary", "recommendations": ["R1"]}},
            1: {"ceo": {"summary": "CEO frames the board"}},
        }
        prompt = build_deliberation_prompt("cto", 2, "Test", prior_outputs, {})
        assert "ROUND 2" in prompt
        assert "agreements" in prompt.lower()
        assert "conflicts" in prompt.lower()
        assert "required_changes" in prompt.lower()

    def test_round_3_includes_all_prior_reports(self):
        """CMO round 3 receives CFO, CTO, CEO round-1, CFO+CTO round-2."""
        prior_outputs = {
            0: {
                "cfo": {"summary": "CFO blind analysis"},
                "cto": {"summary": "CTO blind analysis"},
            },
            1: {"ceo": {"summary": "CEO frames board"}},
            2: {
                "cfo": {"summary": "CFO response", "agreements": ["A"]},
                "cto": {"summary": "CTO response", "conflicts": ["C"]},
            },
        }
        prompt = build_deliberation_prompt("cmo", 3, "Test", prior_outputs, {})
        assert "ROUND 3" in prompt
        assert "CFO blind analysis" in prompt
        assert "CTO blind analysis" in prompt
        assert "challenges_for_" in prompt.lower()

    def test_round_4_includes_full_history(self):
        """Round 4 revision receives all prior deliberation rounds as context."""
        prior_outputs = {
            1: {"ceo": {"summary": "Round 1 CEO"}},
            2: {"cfo": {"summary": "Round 2 CFO"}},
            3: {"cmo": {"summary": "Round 3 CMO"}},
        }
        prompt = build_deliberation_prompt("cfo", 4, "Test", prior_outputs, {})
        assert "ROUND 4" in prompt
        assert "Round 1" in prompt
        assert "Round 2" in prompt
        assert "Round 3" in prompt
        assert "revised_recommendations" in prompt.lower()

    def test_round_5_includes_only_deliberation_rounds(self):
        """Round 5 skips round-0 blind reports."""
        prior_outputs = {
            0: {"ceo": {"title": "Blind CEO report"}},
            1: {"ceo": {"summary": "Round 1 CEO"}},
            2: {"cfo": {"summary": "Round 2 CFO"}},
        }
        prompt = build_deliberation_prompt("ceo", 5, "Test", prior_outputs, {})
        assert "ROUND 5" in prompt
        # Round 0 blind reports should NOT be in round 5 (to keep prompt short)
        assert " Blind CEO report" not in prompt

    def test_round_5_board_decision_schema(self):
        prompt = build_deliberation_prompt("ceo", 5, "Test", {}, {})
        assert "board_decision" in prompt.lower()
        assert "consensus_points" in prompt.lower()
        assert "final_priority_actions" in prompt.lower()
        assert "dissenting_opinions" in prompt.lower()

    def test_round_5_raises_on_unknown_round(self):
        with pytest.raises(ValueError, match="Unknown deliberation round"):
            build_deliberation_prompt("ceo", 99, "Test", {}, {})

    def test_round_5_prompt_stays_concise_with_truncated_summaries(self):
        """Round 5 prompt length should be manageable — summaries are capped."""
        prior_outputs = {
            1: {"ceo": {"summary": "CEO"}},
            2: {"cfo": {"summary": "CFO", "agreements": ["A"], "conflicts": ["C"]}},
            3: {"cmo": {"summary": "CMO"}},
            4: {
                "cfo": {"revised_recommendations": ["R1"]},
                "cto": {"revised_recommendations": ["R2"]},
                "cmo": {"revised_recommendations": ["R3"]},
            },
        }
        prompt = build_deliberation_prompt("ceo", 5, "Test", prior_outputs, {})
        # Entire prompt should fit comfortably under 3000 chars
        assert len(prompt) < 3000

    def test_all_agents_have_deliberation_modifiers(self):
        for agent in ("ceo", "cfo", "cto", "cmo"):
            assert agent in DELIBERATION_MODIFIERS
            modifier = DELIBERATION_MODIFIERS[agent]
            assert isinstance(modifier, str)
            assert len(modifier) > 10
            assert "BOARD MEETING MODE" in modifier.upper() or "board meeting" in modifier.lower()


# -----------------------------------------------------------------------
# DELIBERATION_MODIFIERS
# -----------------------------------------------------------------------

class TestDeliberationModifiers:
    def test_ceo_modifier_mentions_directing_questions(self):
        modifier = DELIBERATION_MODIFIERS["ceo"]
        assert "question" in modifier.lower() or "direct" in modifier.lower()

    def test_cfo_modifier_mentions_citing_numbers(self):
        modifier = DELIBERATION_MODIFIERS["cfo"]
        assert "number" in modifier.lower()

    def test_cto_modifier_mentions_green_yellow_red(self):
        modifier = DELIBERATION_MODIFIERS["cto"]
        assert any(c in modifier for c in ["Green", "Yellow", "Red", "feasibility"])

    def test_cmo_modifier_mentions_customer_segment(self):
        modifier = DELIBERATION_MODIFIERS["cmo"]
        assert "customer" in modifier.lower() or "segment" in modifier.lower()


# -----------------------------------------------------------------------
# DECISION_TYPE_GUIDANCE
# -----------------------------------------------------------------------

class TestDecisionTypeGuidance:
    def test_all_decision_types_have_guidance(self):
        for dtype in ("infrastructure", "pricing", "hiring", "market", "funding", "product"):
            assert dtype in DECISION_TYPE_GUIDANCE
            assert isinstance(DECISION_TYPE_GUIDANCE[dtype], str)
            assert len(DECISION_TYPE_GUIDANCE[dtype]) > 20

    def test_infrastructure_mentions_cto_feasibility(self):
        guidance = DECISION_TYPE_GUIDANCE["infrastructure"]
        assert "CTO" in guidance or "feasibility" in guidance.lower()

    def test_funding_mentions_cfo_modeling(self):
        guidance = DECISION_TYPE_GUIDANCE["funding"]
        assert "CFO" in guidance or "runway" in guidance.lower()