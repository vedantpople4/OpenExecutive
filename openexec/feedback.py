#!/usr/bin/env python3
"""Feedback system for OpenExec - rate recommendations and learn from outcomes."""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class FeedbackSystem:
    """Manages feedback on agent recommendations and tracks learning."""

    def __init__(self, feedback_dir: str = "feedback"):
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(exist_ok=True)

        # Feedback storage
        self.feedback_path = self.feedback_dir / "feedback_log.json"
        self.agent_scores_path = self.feedback_dir / "agent_scores.json"

        self.feedback_log = self._load_feedback()
        self.agent_scores = self._load_agent_scores()

    def _load_feedback(self) -> List[Dict[str, Any]]:
        """Load feedback log from disk."""
        if self.feedback_path.exists():
            with open(self.feedback_path, 'r') as f:
                return json.load(f)
        return []

    def _load_agent_scores(self) -> Dict[str, Dict[str, Any]]:
        """Load agent performance scores from disk."""
        if self.agent_scores_path.exists():
            with open(self.agent_scores_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_feedback(self) -> None:
        """Save feedback log to disk."""
        with open(self.feedback_path, 'w') as f:
            json.dump(self.feedback_log, f, indent=2)

    def _save_agent_scores(self) -> None:
        """Save agent scores to disk."""
        with open(self.agent_scores_path, 'w') as f:
            json.dump(self.agent_scores, f, indent=2)

    def record_feedback(self, decision_id: str, agent: str, recommendation: str,
                       rating: int, outcome: str, notes: str = "") -> str:
        """
        Record feedback on a specific recommendation.

        Args:
            decision_id: ID of the decision
            agent: Agent name (CEO, CFO, CTO, CMO)
            recommendation: The recommendation that was rated
            rating: Rating from 1-5 (1=poor, 5=excellent)
            outcome: What happened when this was implemented
            notes: Additional notes

        Returns:
            feedback_id: Unique ID for this feedback entry
        """
        timestamp = datetime.now().isoformat()
        feedback_id = f"{decision_id}_{agent}_{timestamp}"

        feedback_entry = {
            "id": feedback_id,
            "timestamp": timestamp,
            "decision_id": decision_id,
            "agent": agent,
            "recommendation": recommendation,
            "rating": rating,
            "outcome": outcome,
            "notes": notes
        }

        self.feedback_log.append(feedback_entry)
        self._save_feedback()

        # Update agent scores
        self._update_agent_score(agent, rating, outcome)

        return feedback_id

    def _update_agent_score(self, agent: str, rating: int, outcome: str) -> None:
        """Update agent performance scores based on feedback."""
        if agent not in self.agent_scores:
            self.agent_scores[agent] = {
                "total_ratings": 0,
                "average_rating": 0.0,
                "successful_outcomes": 0,
                "total_feedback": 0,
                "recent_performance": []
            }

        scores = self.agent_scores[agent]

        # Update rating stats
        scores["total_ratings"] += 1
        scores["average_rating"] = (
            (scores["average_rating"] * (scores["total_ratings"] - 1) + rating) /
            scores["total_ratings"]
        )

        # Track successful outcomes
        success_keywords = ["success", "worked", "effective", "positive", "good",
                          "saved", "increased", "improved", "achieved"]
        if any(keyword in outcome.lower() for keyword in success_keywords):
            scores["successful_outcomes"] += 1

        scores["total_feedback"] += 1

        # Keep recent performance (last 10 ratings)
        scores["recent_performance"].append({
            "timestamp": datetime.now().isoformat(),
            "rating": rating,
            "outcome": outcome
        })
        if len(scores["recent_performance"]) > 10:
            scores["recent_performance"].pop(0)

        self._save_agent_scores()

    def get_all_agent_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics for all agents."""
        return self.agent_scores


# Global feedback system instance
feedback_system = FeedbackSystem()