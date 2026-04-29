#!/usr/bin/env python3
"""Memory system for OpenExec - stores conversation embeddings and enables multi-session learning."""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib


class MemorySystem:
    """Manages conversation memory and embeddings for multi-session learning."""

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.memory_dir / "conversations").mkdir(exist_ok=True)
        (self.memory_dir / "embeddings").mkdir(exist_ok=True)
        (self.memory_dir / "decisions").mkdir(exist_ok=True)

        # Memory index
        self.index_path = self.memory_dir / "memory_index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """Load memory index from disk."""
        if self.index_path.exists():
            with open(self.index_path, 'r') as f:
                return json.load(f)
        return {
            "conversations": [],
            "decisions": [],
            "last_updated": None
        }

    def _save_index(self) -> None:
        """Save memory index to disk."""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_path, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _generate_id(self, prompt: str) -> str:
        """Generate a unique ID for a conversation based on prompt hash."""
        return hashlib.md5(prompt.encode()).hexdigest()[:12]

    def store_conversation(self, prompt: str, results: Dict[str, Any]) -> str:
        """Store a conversation and its results in memory."""
        conv_id = self._generate_id(prompt)
        timestamp = datetime.now().isoformat()

        # Store conversation data
        conversation_data = {
            "id": conv_id,
            "timestamp": timestamp,
            "prompt": prompt,
            "executive_summary": results.get('executive_summary', ''),
            "decision_point": results.get('decision_point', ''),
            "synthesized_recommendations": results.get('synthesized_recommendations', []),
            "overall_risk_assessment": results.get('overall_risk_assessment', []),
            "agent_summaries": {}
        }

        # Extract agent summaries
        for agent_name, report in results.get('agent_reports', {}).items():
            conversation_data["agent_summaries"][agent_name] = {
                "title": report.get('title', ''),
                "confidence_score": report.get('confidence_score', 0),
                "key_findings": report.get('key_findings', []),
                "recommendations": report.get('recommendations', [])
            }

        # Save conversation
        conv_path = self.memory_dir / "conversations" / f"{conv_id}.json"
        with open(conv_path, 'w') as f:
            json.dump(conversation_data, f, indent=2)

        # Update index
        self.index["conversations"].append({
            "id": conv_id,
            "timestamp": timestamp,
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
        })

        self._save_index()
        return conv_id

    def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a conversation by ID."""
        conv_path = self.memory_dir / "conversations" / f"{conv_id}.json"
        if conv_path.exists():
            with open(conv_path, 'r') as f:
                return json.load(f)
        return None

    def find_related_conversations(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Find conversations related to a query using keyword matching."""
        related = []

        # Simple keyword matching (in production, would use embeddings)
        query_lower = query.lower()
        keywords = set(query_lower.split())

        for conv_info in self.index["conversations"]:
            conv = self.get_conversation(conv_info["id"])
            if not conv:
                continue

            # Calculate relevance score based on keyword overlap
            score = 0
            text = (conv["prompt"] + " " + conv["executive_summary"]).lower()

            for keyword in keywords:
                if keyword in text:
                    score += 1

            if score > 0:
                related.append({
                    "conversation": conv,
                    "relevance_score": score
                })

        # Sort by relevance and return top results
        related.sort(key=lambda x: x["relevance_score"], reverse=True)
        return [item["conversation"] for item in related[:limit]]

    def get_memory_context(self, query: str) -> str:
        """Generate memory context string for new simulations."""
        related = self.find_related_conversations(query, limit=2)

        if not related:
            return ""

        context_lines = ["## Past Decisions Context\n\n"]

        for i, conv in enumerate(related, 1):
            timestamp = conv["timestamp"]
            prompt = conv["prompt"]
            summary = conv["executive_summary"]

            context_lines.append(f"### Decision {i} ({timestamp})")
            context_lines.append(f"**Question:** {prompt}")
            context_lines.append(f"**Decision:** {summary[:200]}...")
            context_lines.append("")

            # Add key recommendations
            if conv["synthesized_recommendations"]:
                context_lines.append("**Key Recommendations:**")
                for rec in conv["synthesized_recommendations"][:2]:
                    context_lines.append(f"- {rec[:100]}...")
                context_lines.append("")

        return "\n".join(context_lines)

    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        recent = sorted(
            self.index["conversations"],
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]

        return recent

    def search_memory(self, query: str) -> List[Dict[str, Any]]:
        """Search memory for specific topics."""
        results = []
        query_lower = query.lower()

        for conv_info in self.index["conversations"]:
            conv = self.get_conversation(conv_info["id"])
            if not conv:
                continue

            # Search in prompt, summary, and recommendations
            text = (
                conv["prompt"] + " " +
                conv["executive_summary"] + " " +
                " ".join(conv["synthesized_recommendations"])
            ).lower()

            if query_lower in text:
                results.append(conv)

        return results


# Global memory system instance
memory_system = MemorySystem()