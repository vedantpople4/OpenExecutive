"""
Decision tracking and logging system for OpenExec.

This module provides functionality for tracking decisions
made during executive board simulations.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class DecisionTracker:
    """Tracks and logs decisions made during simulations."""

    def __init__(self, log_dir: str = "decisions"):
        """Initialize decision tracker.

        Args:
            log_dir: Directory to store decision logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.decision_log_file = self.log_dir / "decision_log.json"

    def log_decision(self, prompt: str, results: Dict[str, Any], action_items: List[Dict[str, Any]]) -> str:
        """Log a decision with its results and action items.

        Args:
            prompt: The original prompt/question
            results: The simulation results
            action_items: Extracted action items

        Returns:
            Path to the decision log file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        decision_file = self.log_dir / f"decision_{timestamp}.json"

        decision_record = {
            "timestamp": timestamp,
            "prompt": prompt,
            "action_items": action_items,
            "results_summary": self._extract_results_summary(results),
            "file_path": str(decision_file)
        }

        # Write detailed decision file
        with open(decision_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "prompt": prompt,
                "results": results,
                "action_items": action_items
            }, f, indent=2)

        # Add to decision log
        self._update_decision_log(decision_record)

        return str(decision_file)

    def _extract_results_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key summary information from results.

        Args:
            results: The full simulation results

        Returns:
            Summary of key decisions and recommendations
        """
        summary = {
            "executive_summary": results.get("executive_summary", ""),
            "synthesized_recommendations": results.get("synthesized_recommendations", [])[:5],  # Top 5
            "key_risks": results.get("overall_risk_assessment", [])[:3]  # Top 3
        }

        # Extract key findings from each agent
        agent_summaries = {}
        agent_reports = results.get("agent_reports", {})
        for agent_name, report in agent_reports.items():
            agent_summaries[agent_name] = {
                "title": report.get("title", ""),
                "alignment_score": report.get("alignment_score", 0),
                "key_findings": report.get("key_findings", [])[:2]  # Top 2 findings
            }

        summary["agent_summaries"] = agent_summaries
        return summary

    def _update_decision_log(self, decision_record: Dict[str, Any]) -> None:
        """Update the decision log with a new decision record.

        Args:
            decision_record: The decision record to add
        """
        log_data = []

        # Load existing log data
        if self.decision_log_file.exists():
            try:
                with open(self.decision_log_file, 'r') as f:
                    log_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                log_data = []

        # Add new decision record
        log_data.append(decision_record)

        # Keep only the last 100 decisions to prevent file bloat
        if len(log_data) > 100:
            log_data = log_data[-100:]

        # Write updated log
        with open(self.decision_log_file, 'w') as f:
            json.dump(log_data, f, indent=2)

    def get_decision_history(self) -> List[Dict[str, Any]]:
        """Get decision history.

        Returns:
            List of decision records
        """
        if not self.decision_log_file.exists():
            return []

        try:
            with open(self.decision_log_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent decisions.

        Args:
            limit: Number of recent decisions to return

        Returns:
            List of recent decision records, sorted by timestamp (most recent first)
        """
        history = self.get_decision_history()
        if not history:
            return []
        # Get last N items and reverse to get most recent first
        recent = history[-limit:]
        return list(reversed(recent))

    def find_related_decisions(self, query: str) -> List[Dict[str, Any]]:
        """Find decisions related to a query.

        Args:
            query: Search query

        Returns:
            List of related decisions
        """
        history = self.get_decision_history()
        related = []

        query_lower = query.lower()
        for decision in history:
            if (query_lower in decision.get("prompt", "").lower() or
                any(query_lower in item.get("task", "").lower() for item in decision.get("action_items", []))):
                related.append(decision)

        return related


# Global decision tracker instance
decision_tracker = DecisionTracker()