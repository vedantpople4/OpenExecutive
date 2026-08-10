"""Tests for src/feedback.py — FeedbackSystem class."""

import pytest
import json
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

        FeedbackSystem(feedback_dir=str(feedback_dir))
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





