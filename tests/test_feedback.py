"""Tests for src/feedback.py — FeedbackSystem class."""

import pytest
import json
from pathlib import Path
from datetime import datetime
from openexec.feedback import FeedbackSystem


@pytest.fixture
def temp_feedback_system(tmp_path):
    """Create a FeedbackSystem with a temporary directory."""
    system = FeedbackSystem(feedback_dir=str(tmp_path))
    return system


@pytest.fixture
def sample_results():
    """Sample simulation results for testing."""
    return {
        "executive_summary": "Test decision summary",
        "agent_reports": {
            "ceo": {
                "alignment_score": 0.8,
                "recommendations": [
                    "Implement the strategy",
                    "Establish a timeline",
                    "Create a plan"
                ]
            },
            "cfo": {
                "alignment_score": 0.7,
                "recommendations": [
                    "Allocate budget",
                    "Monitor expenses"
                ]
            }
        }
    }


class TestFeedbackSystemInitialization:
    """FeedbackSystem initialization and setup."""

    def test_creates_feedback_directory(self, tmp_path):
        """Should create feedback directory if it doesn't exist."""
        feedback_dir = tmp_path / "feedback"
        assert not feedback_dir.exists()

        system = FeedbackSystem(feedback_dir=str(feedback_dir))
        assert feedback_dir.exists()
        assert feedback_dir.is_dir()

    def test_initializes_empty_feedback_log(self, temp_feedback_system):
        """Should initialize empty feedback log."""
        assert temp_feedback_system.feedback_log == []

    def test_initializes_empty_agent_scores(self, temp_feedback_system):
        """Should initialize empty agent scores."""
        assert temp_feedback_system.agent_scores == {}


class TestRecordFeedback:
    """record_feedback() — recording feedback on recommendations."""

    def test_records_feedback(self, temp_feedback_system):
        """Should record feedback and return feedback ID."""
        feedback_id = temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Implement the strategy",
            rating=5,
            outcome="Successfully implemented"
        )

        assert feedback_id is not None
        assert "decision_001" in feedback_id
        assert "CEO" in feedback_id

    def test_saves_feedback_to_log(self, temp_feedback_system):
        """Should save feedback to feedback log."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Implement the strategy",
            rating=5,
            outcome="Successfully implemented"
        )

        assert len(temp_feedback_system.feedback_log) == 1
        assert temp_feedback_system.feedback_log[0]["agent"] == "CEO"
        assert temp_feedback_system.feedback_log[0]["rating"] == 5

    def test_updates_agent_scores(self, temp_feedback_system):
        """Should update agent scores when recording feedback."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Implement the strategy",
            rating=5,
            outcome="Successfully implemented"
        )

        assert "CEO" in temp_feedback_system.agent_scores
        scores = temp_feedback_system.agent_scores["CEO"]
        assert scores["total_ratings"] == 1
        assert scores["average_rating"] == 5.0

    def test_multiple_feedback_updates_average(self, temp_feedback_system):
        """Multiple feedback entries should update average correctly."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Task 1",
            rating=5,
            outcome="Success"
        )
        temp_feedback_system.record_feedback(
            decision_id="decision_002",
            agent="CEO",
            recommendation="Task 2",
            rating=3,
            outcome="Partial success"
        )

        scores = temp_feedback_system.agent_scores["CEO"]
        assert scores["total_ratings"] == 2
        assert scores["average_rating"] == 4.0  # (5 + 3) / 2

    def test_tracks_successful_outcomes(self, temp_feedback_system):
        """Should track successful outcomes based on keywords."""
        success_keywords = ["success", "worked", "effective", "positive", "good"]

        for keyword in success_keywords:
            temp_feedback_system.record_feedback(
                decision_id=f"decision_{keyword}",
                agent="CEO",
                recommendation="Test",
                rating=5,
                outcome=f"This {keyword}"
            )

        scores = temp_feedback_system.agent_scores["CEO"]
        assert scores["successful_outcomes"] == len(success_keywords)

    def test_tracks_recent_performance(self, temp_feedback_system):
        """Should track recent performance (last 10 ratings)."""
        # Add 15 feedback entries
        for i in range(15):
            temp_feedback_system.record_feedback(
                decision_id=f"decision_{i}",
                agent="CEO",
                recommendation=f"Task {i}",
                rating=i % 5 + 1,
                outcome="Test"
            )

        scores = temp_feedback_system.agent_scores["CEO"]
        assert len(scores["recent_performance"]) == 10

    def test_saves_to_disk(self, temp_feedback_system):
        """Should save feedback and scores to disk."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Test",
            rating=5,
            outcome="Success"
        )

        # Check files exist
        assert temp_feedback_system.feedback_path.exists()
        assert temp_feedback_system.agent_scores_path.exists()

        # Check content
        with open(temp_feedback_system.feedback_path, 'r') as f:
            log_data = json.load(f)
        assert len(log_data) == 1

        with open(temp_feedback_system.agent_scores_path, 'r') as f:
            scores_data = json.load(f)
        assert "CEO" in scores_data


class TestGetAgentPerformance:
    """get_agent_performance() — retrieving agent performance metrics."""

    def test_returns_none_for_unknown_agent(self, temp_feedback_system):
        """Should return None for agent with no feedback."""
        performance = temp_feedback_system.get_agent_performance("UNKNOWN")
        assert performance is None

    def test_returns_performance_for_known_agent(self, temp_feedback_system):
        """Should return performance metrics for known agent."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Test",
            rating=5,
            outcome="Success"
        )

        performance = temp_feedback_system.get_agent_performance("CEO")
        assert performance is not None
        assert performance["total_ratings"] == 1
        assert performance["average_rating"] == 5.0

    def test_returns_all_metrics(self, temp_feedback_system):
        """Should return all performance metrics."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Test",
            rating=5,
            outcome="Success"
        )

        performance = temp_feedback_system.get_agent_performance("CEO")
        assert "total_ratings" in performance
        assert "average_rating" in performance
        assert "successful_outcomes" in performance
        assert "total_feedback" in performance
        assert "recent_performance" in performance


class TestGetAllAgentPerformance:
    """get_all_agent_performance() — retrieving all agent performance."""

    def test_returns_empty_dict_initially(self, temp_feedback_system):
        """Should return empty dict when no feedback recorded."""
        all_performance = temp_feedback_system.get_all_agent_performance()
        assert all_performance == {}

    def test_returns_all_agents(self, temp_feedback_system):
        """Should return performance for all agents."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Test",
            rating=5,
            outcome="Success"
        )
        temp_feedback_system.record_feedback(
            decision_id="decision_002",
            agent="CFO",
            recommendation="Test",
            rating=4,
            outcome="Success"
        )

        all_performance = temp_feedback_system.get_all_agent_performance()
        assert "CEO" in all_performance
        assert "CFO" in all_performance
        assert len(all_performance) == 2


class TestGetFeedbackForDecision:
    """get_feedback_for_decision() — retrieving feedback for specific decision."""

    def test_returns_empty_for_unknown_decision(self, temp_feedback_system):
        """Should return empty list for unknown decision."""
        feedback = temp_feedback_system.get_feedback_for_decision("unknown_decision")
        assert feedback == []

    def test_returns_feedback_for_decision(self, temp_feedback_system):
        """Should return all feedback for a specific decision."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Task 1",
            rating=5,
            outcome="Success"
        )
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CFO",
            recommendation="Task 2",
            rating=4,
            outcome="Success"
        )
        temp_feedback_system.record_feedback(
            decision_id="decision_002",
            agent="CEO",
            recommendation="Task 3",
            rating=3,
            outcome="Partial"
        )

        feedback = temp_feedback_system.get_feedback_for_decision("decision_001")
        assert len(feedback) == 2
        assert all(f["decision_id"] == "decision_001" for f in feedback)


class TestGetTopRecommendations:
    """get_top_recommendations() — retrieving top-rated recommendations."""

    def test_returns_empty_for_unknown_agent(self, temp_feedback_system):
        """Should return empty list for agent with no feedback."""
        top = temp_feedback_system.get_top_recommendations("UNKNOWN")
        assert top == []

    def test_returns_top_rated_recommendations(self, temp_feedback_system):
        """Should return top-rated recommendations sorted by rating."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Task 1",
            rating=5,
            outcome="Success"
        )
        temp_feedback_system.record_feedback(
            decision_id="decision_002",
            agent="CEO",
            recommendation="Task 2",
            rating=3,
            outcome="Partial"
        )
        temp_feedback_system.record_feedback(
            decision_id="decision_003",
            agent="CEO",
            recommendation="Task 3",
            rating=4,
            outcome="Success"
        )

        top = temp_feedback_system.get_top_recommendations("CEO", limit=2)
        assert len(top) == 2
        assert top[0]["rating"] == 5
        assert top[1]["rating"] == 4

    def test_respects_limit_parameter(self, temp_feedback_system):
        """Should respect the limit parameter."""
        for i in range(10):
            temp_feedback_system.record_feedback(
                decision_id=f"decision_{i}",
                agent="CEO",
                recommendation=f"Task {i}",
                rating=i % 5 + 1,
                outcome="Test"
            )

        top = temp_feedback_system.get_top_recommendations("CEO", limit=3)
        assert len(top) == 3


class TestGetLearningInsights:
    """get_learning_insights() — generating learning insights for agents."""

    def test_returns_message_for_unknown_agent(self, temp_feedback_system):
        """Should return message for agent with no feedback."""
        insights = temp_feedback_system.get_learning_insights("UNKNOWN")
        assert "No feedback data available" in insights

    def test_generates_insights_for_agent(self, temp_feedback_system):
        """Should generate insights for agent with feedback."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Task 1",
            rating=5,
            outcome="Successfully implemented"
        )

        insights = temp_feedback_system.get_learning_insights("CEO")
        assert "CEO Performance Insights" in insights
        assert "Average Rating:" in insights
        assert "Total Ratings:" in insights
        assert "Success Rate:" in insights

    def test_includes_top_recommendations(self, temp_feedback_system):
        """Should include top performing recommendations."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Top recommendation",
            rating=5,
            outcome="Successfully implemented"
        )

        insights = temp_feedback_system.get_learning_insights("CEO")
        assert "Top Performing Recommendations:" in insights

    def test_includes_recent_trend(self, temp_feedback_system):
        """Should include recent performance trend."""
        temp_feedback_system.record_feedback(
            decision_id="decision_001",
            agent="CEO",
            recommendation="Task 1",
            rating=5,
            outcome="Success"
        )

        insights = temp_feedback_system.get_learning_insights("CEO")
        assert "Recent Trend:" in insights


class TestGenerateFeedbackPrompt:
    """generate_feedback_prompt() — generating feedback collection prompt."""

    def test_generates_prompt_with_decision_id(self, temp_feedback_system, sample_results):
        """Should generate prompt with decision ID."""
        prompt = temp_feedback_system.generate_feedback_prompt("decision_001", sample_results)
        assert "Decision ID: decision_001" in prompt

    def test_generates_prompt_with_decision_summary(self, temp_feedback_system, sample_results):
        """Should generate prompt with decision summary."""
        prompt = temp_feedback_system.generate_feedback_prompt("decision_001", sample_results)
        assert "Test decision summary" in prompt

    def test_includes_agent_reports(self, temp_feedback_system, sample_results):
        """Should include agent reports in prompt."""
        prompt = temp_feedback_system.generate_feedback_prompt("decision_001", sample_results)
        assert "CEO" in prompt
        assert "CFO" in prompt

    def test_includes_alignment_scores(self, temp_feedback_system, sample_results):
        """Should include alignment scores in prompt."""
        prompt = temp_feedback_system.generate_feedback_prompt("decision_001", sample_results)
        assert "80%" in prompt  # CEO's 0.8 alignment score
        assert "70%" in prompt  # CFO's 0.7 alignment score

    def test_includes_recommendations(self, temp_feedback_system, sample_results):
        """Should include recommendations in prompt."""
        prompt = temp_feedback_system.generate_feedback_prompt("decision_001", sample_results)
        assert "Implement the strategy" in prompt
        assert "Allocate budget" in prompt

    def test_includes_rating_instructions(self, temp_feedback_system, sample_results):
        """Should include rating instructions."""
        prompt = temp_feedback_system.generate_feedback_prompt("decision_001", sample_results)
        assert "Rating (1-5)" in prompt
        assert "What happened when implemented?" in prompt
