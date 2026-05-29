"""Tests for src/utils.py — utility functions."""

import pytest
from src.utils import extract_action_items


class TestExtractActionItems:
    """extract_action_items() — action item extraction from results."""

    def test_empty_results(self):
        """Empty results should return empty list."""
        results = {}
        actions = extract_action_items(results)
        assert actions == []

    def test_no_synthesized_recommendations(self):
        """Results without synthesized recommendations should still extract from agent reports."""
        results = {
            "synthesized_recommendations": [],
            "agent_reports": {
                "ceo": {
                    "recommendations": [
                        "Implement the new strategy",
                        "Establish a timeline"
                    ]
                }
            }
        }
        actions = extract_action_items(results)
        assert len(actions) == 2
        assert actions[0]["owner"] == "CEO"
        assert actions[0]["priority"] == "HIGH"

    def test_synthesized_recommendations_with_owner(self):
        """Synthesized recommendations with [OWNER] format should be parsed correctly."""
        results = {
            "synthesized_recommendations": [
                "[CEO] Implement the strategic plan",
                "[CFO] Allocate budget for Q2",
                "[CTO] Build the infrastructure",
                "[CMO] Launch marketing campaign"
            ]
        }
        actions = extract_action_items(results)
        assert len(actions) == 4

        # Check CEO action
        ceo_action = next(a for a in actions if a["owner"] == "CEO")
        assert ceo_action["task"] == "Implement the strategic plan"
        assert ceo_action["priority"] == "HIGH"

        # Check CFO action
        cfo_action = next(a for a in actions if a["owner"] == "CFO")
        assert cfo_action["task"] == "Allocate budget for Q2"
        assert cfo_action["priority"] == "HIGH"

        # Check CTO action
        cto_action = next(a for a in actions if a["owner"] == "CTO")
        assert cto_action["task"] == "Build the infrastructure"
        assert cto_action["priority"] == "MEDIUM"

        # Check CMO action
        cmo_action = next(a for a in actions if a["owner"] == "CMO")
        assert cmo_action["task"] == "Launch marketing campaign"
        assert cmo_action["priority"] == "MEDIUM"

    def test_priority_mapping(self):
        """Priority should be mapped correctly based on owner."""
        results = {
            "synthesized_recommendations": [
                "[CEO] CEO task",
                "[CFO] CFO task",
                "[CTO] CTO task",
                "[CMO] CMO task",
                "[Unknown] Unknown task"
            ]
        }
        actions = extract_action_items(results)

        # Check priorities
        priorities = {a["owner"]: a["priority"] for a in actions}
        assert priorities["CEO"] == "HIGH"
        assert priorities["CFO"] == "HIGH"
        assert priorities["CTO"] == "MEDIUM"
        assert priorities["CMO"] == "MEDIUM"
        assert priorities["Unknown"] == "MEDIUM"  # default

    def test_action_keywords_detection(self):
        """Actionable language should be detected in agent recommendations."""
        results = {
            "synthesized_recommendations": [],
            "agent_reports": {
                "ceo": {
                    "recommendations": [
                        "implement the strategy",
                        "Establish a timeline",
                        "create a plan",
                        "develop the product",
                        "build the team",
                        "allocate resources",
                        "prioritize tasks",
                        "focus on growth",
                        "dedicate time",
                        "just a comment"  # not actionable
                    ]
                }
            }
        }
        actions = extract_action_items(results)

        # Should extract 9 actionable items (not the last one)
        assert len(actions) == 9
        assert all(a["owner"] == "CEO" for a in actions)

    def test_capitalization_correction(self):
        """Lowercase recommendations should be capitalized."""
        results = {
            "synthesized_recommendations": [],
            "agent_reports": {
                "cfo": {
                    "recommendations": [
                        "implement the budget",
                        "Establish the timeline"
                    ]
                }
            }
        }
        actions = extract_action_items(results)

        assert len(actions) == 2
        assert actions[0]["task"] == "Implement the budget"  # capitalized
        assert actions[1]["task"] == "Establish the timeline"  # already capitalized

    def test_due_date_default(self):
        """All action items should have TBD as default due date."""
        results = {
            "synthesized_recommendations": ["[CEO] Test task"]
        }
        actions = extract_action_items(results)

        assert all(a["due_date"] == "TBD" for a in actions)

    def test_mixed_sources(self):
        """Should extract from both synthesized and agent recommendations."""
        results = {
            "synthesized_recommendations": [
                "[CEO] Synthesized task"
            ],
            "agent_reports": {
                "cfo": {
                    "recommendations": ["implement the budget"]
                }
            }
        }
        actions = extract_action_items(results)

        assert len(actions) == 2
        owners = {a["owner"] for a in actions}
        assert "CEO" in owners
        assert "CFO" in owners

    def test_malformed_recommendation_format(self):
        """Should handle malformed recommendation format gracefully."""
        results = {
            "synthesized_recommendations": [
                "No brackets here",
                "[Missing closing bracket",
                "Just text"
            ]
        }
        actions = extract_action_items(results)

        # Should not crash, but may not extract properly
        # The function should handle this gracefully
        assert isinstance(actions, list)

    def test_empty_agent_reports(self):
        """Empty agent reports should not cause errors."""
        results = {
            "synthesized_recommendations": ["[CEO] Test task"],
            "agent_reports": {}
        }
        actions = extract_action_items(results)

        assert len(actions) == 1
        assert actions[0]["owner"] == "CEO"

    def test_case_insensitive_owner_matching(self):
        """Owner matching should be case-insensitive."""
        results = {
            "synthesized_recommendations": [
                "[ceo] CEO task",
                "[CFO] CFO task",
                "[cto] CTO task"
            ]
        }
        actions = extract_action_items(results)

        priorities = {a["owner"]: a["priority"] for a in actions}
        assert priorities["CEO"] == "HIGH"
        assert priorities["CFO"] == "HIGH"
        assert priorities["CTO"] == "MEDIUM"
