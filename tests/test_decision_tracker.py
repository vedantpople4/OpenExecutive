"""Tests for src/decision_tracker.py — DecisionTracker class."""

import pytest
import json
from pathlib import Path
from openexec.decision_tracker import DecisionTracker


@pytest.fixture
def temp_tracker(tmp_path):
    """Create a DecisionTracker with a temporary directory."""
    tracker = DecisionTracker(log_dir=str(tmp_path))
    return tracker


@pytest.fixture
def sample_results():
    """Sample simulation results for testing."""
    return {
        "executive_summary": "Test decision summary",
        "decision_point": "Test decision point",
        "synthesized_recommendations": [
            "[CEO] Implement strategy",
            "[CFO] Allocate budget"
        ],
        "overall_risk_assessment": [
            "Risk 1",
            "Risk 2",
            "Risk 3"
        ],
        "agent_reports": {
            "ceo": {
                "title": "CEO Report",
                "alignment_score": 0.8,
                "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
                "recommendations": ["Rec 1", "Rec 2"]
            },
            "cfo": {
                "title": "CFO Report",
                "alignment_score": 0.7,
                "key_findings": ["Finding A", "Finding B"],
                "recommendations": ["Rec A"]
            }
        }
    }


@pytest.fixture
def sample_action_items():
    """Sample action items for testing."""
    return [
        {
            "priority": "HIGH",
            "task": "Implement strategy",
            "owner": "CEO",
            "due_date": "TBD"
        },
        {
            "priority": "HIGH",
            "task": "Allocate budget",
            "owner": "CFO",
            "due_date": "TBD"
        }
    ]


class TestDecisionTrackerInitialization:
    """DecisionTracker initialization and setup."""

    def test_creates_log_directory(self, tmp_path):
        """Should create log directory if it doesn't exist."""
        log_dir = tmp_path / "decisions"
        assert not log_dir.exists()

        DecisionTracker(log_dir=str(log_dir))
        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_initializes_log_file_path(self, temp_tracker):
        """Should initialize decision log file path."""
        assert temp_tracker.decision_log_file.exists() is False
        assert temp_tracker.decision_log_file.name == "decision_log.json"


class TestLogDecision:
    """log_decision() — logging decisions with results and action items."""

    def test_logs_decision_to_file(self, temp_tracker, sample_results, sample_action_items):
        """Should log decision to a timestamped file."""
        file_path = temp_tracker.log_decision(
            prompt="Test prompt",
            results=sample_results,
            action_items=sample_action_items
        )

        assert Path(file_path).exists()
        assert file_path.endswith(".json")

    def test_decision_file_contains_all_data(self, temp_tracker, sample_results, sample_action_items):
        """Decision file should contain all provided data."""
        file_path = temp_tracker.log_decision(
            prompt="Test prompt",
            results=sample_results,
            action_items=sample_action_items
        )

        with open(file_path, 'r') as f:
            data = json.load(f)

        assert data["prompt"] == "Test prompt"
        assert data["results"] == sample_results
        assert data["action_items"] == sample_action_items
        assert "timestamp" in data

    def test_updates_decision_log(self, temp_tracker, sample_results, sample_action_items):
        """Should update the main decision log."""
        temp_tracker.log_decision(
            prompt="Test prompt",
            results=sample_results,
            action_items=sample_action_items
        )

        assert temp_tracker.decision_log_file.exists()

        with open(temp_tracker.decision_log_file, 'r') as f:
            log_data = json.load(f)

        assert len(log_data) == 1
        assert log_data[0]["prompt"] == "Test prompt"

    def test_multiple_decisions_in_log(self, temp_tracker, sample_results, sample_action_items):
        """Should handle multiple decisions in the log."""
        for i in range(3):
            temp_tracker.log_decision(
                prompt=f"Test prompt {i}",
                results=sample_results,
                action_items=sample_action_items
            )

        with open(temp_tracker.decision_log_file, 'r') as f:
            log_data = json.load(f)

        assert len(log_data) == 3

    def test_log_keeps_only_last_100_decisions(self, temp_tracker, sample_results, sample_action_items):
        """Should keep only the last 100 decisions to prevent file bloat."""
        # Log 105 decisions
        for i in range(105):
            temp_tracker.log_decision(
                prompt=f"Test prompt {i}",
                results=sample_results,
                action_items=sample_action_items
            )

        with open(temp_tracker.decision_log_file, 'r') as f:
            log_data = json.load(f)

        assert len(log_data) == 100
        # Should keep the last 100 (prompts 5-104)
        assert log_data[0]["prompt"] == "Test prompt 5"
        assert log_data[-1]["prompt"] == "Test prompt 104"


class TestExtractResultsSummary:
    """_extract_results_summary() — extracting summary from results."""

    def test_extracts_executive_summary(self, temp_tracker, sample_results):
        """Should extract executive summary."""
        summary = temp_tracker._extract_results_summary(sample_results)

        assert summary["executive_summary"] == "Test decision summary"

    def test_limits_synthesized_recommendations(self, temp_tracker, sample_results):
        """Should limit synthesized recommendations to top 5."""
        results = sample_results.copy()
        results["synthesized_recommendations"] = [f"Rec {i}" for i in range(10)]

        summary = temp_tracker._extract_results_summary(results)

        assert len(summary["synthesized_recommendations"]) == 5
        assert summary["synthesized_recommendations"] == [f"Rec {i}" for i in range(5)]

    def test_limits_key_risks(self, temp_tracker, sample_results):
        """Should limit key risks to top 3."""
        results = sample_results.copy()
        results["overall_risk_assessment"] = [f"Risk {i}" for i in range(10)]

        summary = temp_tracker._extract_results_summary(results)

        assert len(summary["key_risks"]) == 3
        assert summary["key_risks"] == [f"Risk {i}" for i in range(3)]

    def test_extracts_agent_summaries(self, temp_tracker, sample_results):
        """Should extract summaries for each agent."""
        summary = temp_tracker._extract_results_summary(sample_results)

        assert "agent_summaries" in summary
        assert "ceo" in summary["agent_summaries"]
        assert "cfo" in summary["agent_summaries"]

        ceo_summary = summary["agent_summaries"]["ceo"]
        assert ceo_summary["title"] == "CEO Report"
        assert ceo_summary["alignment_score"] == 0.8
        assert len(ceo_summary["key_findings"]) == 2  # limited to top 2

    def test_handles_missing_fields(self, temp_tracker):
        """Should handle missing fields gracefully."""
        results = {}

        summary = temp_tracker._extract_results_summary(results)

        assert summary["executive_summary"] == ""
        assert summary["synthesized_recommendations"] == []
        assert summary["key_risks"] == []
        assert summary["agent_summaries"] == {}




