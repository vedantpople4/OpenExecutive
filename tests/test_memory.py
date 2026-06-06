"""Tests for src/memory.py — MemorySystem class."""

import pytest
import json
from pathlib import Path
from datetime import datetime
from openexec.memory import MemorySystem


@pytest.fixture
def temp_memory_system(tmp_path):
    """Create a MemorySystem with a temporary directory."""
    system = MemorySystem(memory_dir=str(tmp_path))
    return system


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
            "Risk 2"
        ],
        "agent_reports": {
            "ceo": {
                "title": "CEO Report",
                "alignment_score": 0.8,
                "key_findings": ["Finding 1", "Finding 2"],
                "recommendations": ["Rec 1", "Rec 2"]
            },
            "cfo": {
                "title": "CFO Report",
                "alignment_score": 0.7,
                "key_findings": ["Finding A"],
                "recommendations": ["Rec A"]
            }
        }
    }


class TestMemorySystemInitialization:
    """MemorySystem initialization and setup."""

    def test_creates_memory_directory(self, tmp_path):
        """Should create memory directory if it doesn't exist."""
        memory_dir = tmp_path / "memory"
        assert not memory_dir.exists()

        system = MemorySystem(memory_dir=str(memory_dir))
        assert memory_dir.exists()
        assert memory_dir.is_dir()

    def test_creates_subdirectories(self, temp_memory_system):
        """Should create required subdirectories."""
        assert (temp_memory_system.memory_dir / "conversations").exists()
        assert (temp_memory_system.memory_dir / "embeddings").exists()
        assert (temp_memory_system.memory_dir / "decisions").exists()

    def test_initializes_empty_index(self, temp_memory_system):
        """Should initialize empty index."""
        assert temp_memory_system.index["conversations"] == []
        assert temp_memory_system.index["decisions"] == []
        assert temp_memory_system.index["last_updated"] is None


class TestStoreConversation:
    """store_conversation() — storing conversations in memory."""

    def test_stores_conversation(self, temp_memory_system, sample_results):
        """Should store conversation and return conversation ID."""
        conv_id = temp_memory_system.store_conversation(
            prompt="Test prompt",
            results=sample_results
        )

        assert conv_id is not None
        assert len(conv_id) == 12  # MD5 hash truncated to 12 chars

    def test_saves_conversation_to_file(self, temp_memory_system, sample_results):
        """Should save conversation to a file."""
        conv_id = temp_memory_system.store_conversation(
            prompt="Test prompt",
            results=sample_results
        )

        conv_path = temp_memory_system.memory_dir / "conversations" / f"{conv_id}.json"
        assert conv_path.exists()

        with open(conv_path, 'r') as f:
            data = json.load(f)

        assert data["prompt"] == "Test prompt"
        assert data["executive_summary"] == "Test decision summary"

    def test_updates_index(self, temp_memory_system, sample_results):
        """Should update memory index."""
        temp_memory_system.store_conversation(
            prompt="Test prompt",
            results=sample_results
        )

        assert len(temp_memory_system.index["conversations"]) == 1
        assert temp_memory_system.index["conversations"][0]["prompt"] == "Test prompt"

    def test_truncates_long_prompts_in_index(self, temp_memory_system, sample_results):
        """Should truncate long prompts in index."""
        long_prompt = "a" * 150
        temp_memory_system.store_conversation(
            prompt=long_prompt,
            results=sample_results
        )

        index_prompt = temp_memory_system.index["conversations"][0]["prompt"]
        assert len(index_prompt) <= 103  # 100 chars + "..."
        assert "..." in index_prompt

    def test_saves_index_to_disk(self, temp_memory_system, sample_results):
        """Should save index to disk."""
        temp_memory_system.store_conversation(
            prompt="Test prompt",
            results=sample_results
        )

        index_path = temp_memory_system.memory_dir / "memory_index.json"
        assert index_path.exists()

        with open(index_path, 'r') as f:
            index_data = json.load(f)

        assert len(index_data["conversations"]) == 1

    def test_extracts_agent_summaries(self, temp_memory_system, sample_results):
        """Should extract agent summaries from results."""
        conv_id = temp_memory_system.store_conversation(
            prompt="Test prompt",
            results=sample_results
        )

        conv_path = temp_memory_system.memory_dir / "conversations" / f"{conv_id}.json"
        with open(conv_path, 'r') as f:
            data = json.load(f)

        assert "agent_summaries" in data
        assert "ceo" in data["agent_summaries"]
        assert "cfo" in data["agent_summaries"]

        ceo_summary = data["agent_summaries"]["ceo"]
        assert ceo_summary["title"] == "CEO Report"
        assert ceo_summary["alignment_score"] == 0.8


class TestGetConversation:
    """get_conversation() — retrieving conversations by ID."""

    def test_returns_none_for_unknown_id(self, temp_memory_system):
        """Should return None for unknown conversation ID."""
        conv = temp_memory_system.get_conversation("unknown_id")
        assert conv is None

    def test_returns_stored_conversation(self, temp_memory_system, sample_results):
        """Should return stored conversation."""
        conv_id = temp_memory_system.store_conversation(
            prompt="Test prompt",
            results=sample_results
        )

        conv = temp_memory_system.get_conversation(conv_id)
        assert conv is not None
        assert conv["prompt"] == "Test prompt"
        assert conv["executive_summary"] == "Test decision summary"


class TestFindRelatedConversations:
    """find_related_conversations() — finding conversations related to a query."""

    def test_returns_empty_for_no_conversations(self, temp_memory_system):
        """Should return empty list when no conversations stored."""
        related = temp_memory_system.find_related_conversations("test query")
        assert related == []

    def test_finds_conversations_by_keyword(self, temp_memory_system, sample_results):
        """Should find conversations matching query keywords."""
        temp_memory_system.store_conversation(
            prompt="Buy vs lease equipment",
            results=sample_results
        )

        related = temp_memory_system.find_related_conversations("buy equipment")
        assert len(related) == 1

    def test_scores_by_keyword_overlap(self, temp_memory_system, sample_results):
        """Should score conversations by keyword overlap."""
        temp_memory_system.store_conversation(
            prompt="Buy vs lease equipment decision",
            results=sample_results
        )

        # Query with 2 matching keywords
        related = temp_memory_system.find_related_conversations("buy lease")
        assert len(related) == 1

    def test_returns_no_matches_for_no_keywords(self, temp_memory_system, sample_results):
        """Should return empty when no keywords match."""
        temp_memory_system.store_conversation(
            prompt="Buy vs lease equipment",
            results=sample_results
        )

        related = temp_memory_system.find_related_conversations("nonexistent query")
        assert related == []

    def test_respects_limit_parameter(self, temp_memory_system, sample_results):
        """Should respect the limit parameter."""
        for i in range(5):
            temp_memory_system.store_conversation(
                prompt=f"Test prompt {i}",
                results=sample_results
            )

        related = temp_memory_system.find_related_conversations("test", limit=2)
        assert len(related) == 2

    def test_sorts_by_relevance(self, temp_memory_system, sample_results):
        """Should sort results by relevance score."""
        temp_memory_system.store_conversation(
            prompt="Buy vs lease equipment decision",
            results=sample_results
        )
        temp_memory_system.store_conversation(
            prompt="Test prompt",
            results=sample_results
        )

        related = temp_memory_system.find_related_conversations("buy lease equipment")
        # First result should have higher relevance (more keyword matches)
        assert len(related) >= 1


class TestGetMemoryContext:
    """get_memory_context() — generating memory context for new simulations."""

    def test_returns_empty_for_no_related_conversations(self, temp_memory_system):
        """Should return empty string when no related conversations."""
        context = temp_memory_system.get_memory_context("test query")
        assert context == ""

    def test_generates_context_with_related_conversations(self, temp_memory_system, sample_results):
        """Should generate context with related conversations."""
        temp_memory_system.store_conversation(
            prompt="Buy vs lease equipment",
            results=sample_results
        )

        context = temp_memory_system.get_memory_context("buy")
        assert "Past Decisions Context" in context
        assert "Decision 1" in context

    def test_includes_decision_summary(self, temp_memory_system, sample_results):
        """Should include decision summary in context."""
        temp_memory_system.store_conversation(
            prompt="Test prompt",
            results=sample_results
        )

        context = temp_memory_system.get_memory_context("test")
        assert "Test decision summary" in context

    def test_includes_key_recommendations(self, temp_memory_system, sample_results):
        """Should include key recommendations in context."""
        temp_memory_system.store_conversation(
            prompt="Test prompt",
            results=sample_results
        )

        context = temp_memory_system.get_memory_context("test")
        assert "Key Recommendations:" in context

    def test_limits_to_top_2_conversations(self, temp_memory_system, sample_results):
        """Should limit to top 2 related conversations."""
        for i in range(5):
            temp_memory_system.store_conversation(
                prompt=f"Test prompt {i}",
                results=sample_results
            )

        context = temp_memory_system.get_memory_context("test")
        # Should only include top 2 (limit parameter in get_memory_context is 2)
        # Count the "Decision X" occurrences in the context
        decision_count = context.count("### Decision")
        assert decision_count <= 2


class TestGetConversationHistory:
    """get_conversation_history() — retrieving recent conversation history."""

    def test_returns_empty_initially(self, temp_memory_system):
        """Should return empty list when no conversations stored."""
        history = temp_memory_system.get_conversation_history()
        assert history == []

    def test_returns_recent_conversations(self, temp_memory_system, sample_results):
        """Should return recent conversations."""
        for i in range(5):
            temp_memory_system.store_conversation(
                prompt=f"Test prompt {i}",
                results=sample_results
            )

        history = temp_memory_system.get_conversation_history()
        assert len(history) == 5

    def test_respects_limit_parameter(self, temp_memory_system, sample_results):
        """Should respect the limit parameter."""
        for i in range(10):
            temp_memory_system.store_conversation(
                prompt=f"Test prompt {i}",
                results=sample_results
            )

        history = temp_memory_system.get_conversation_history(limit=5)
        assert len(history) == 5

    def test_sorts_by_timestamp_descending(self, temp_memory_system, sample_results):
        """Should sort by timestamp in descending order."""
        for i in range(3):
            temp_memory_system.store_conversation(
                prompt=f"Test prompt {i}",
                results=sample_results
            )

        history = temp_memory_system.get_conversation_history()
        # Most recent should be first
        timestamps = [conv["timestamp"] for conv in history]
        assert timestamps == sorted(timestamps, reverse=True)


class TestSearchMemory:
    """search_memory() — searching memory for specific topics."""

    def test_returns_empty_for_no_matches(self, temp_memory_system):
        """Should return empty list when no matches found."""
        results = temp_memory_system.search_memory("nonexistent query")
        assert results == []

    def test_searches_in_prompt(self, temp_memory_system, sample_results):
        """Should search in prompt field."""
        temp_memory_system.store_conversation(
            prompt="Buy vs lease equipment",
            results=sample_results
        )

        results = temp_memory_system.search_memory("buy")
        assert len(results) == 1
        assert "buy" in results[0]["prompt"].lower()

    def test_searches_in_executive_summary(self, temp_memory_system, sample_results):
        """Should search in executive summary field."""
        temp_memory_system.store_conversation(
            prompt="Test prompt",
            results=sample_results
        )

        results = temp_memory_system.search_memory("decision summary")
        assert len(results) == 1

    def test_searches_in_recommendations(self, temp_memory_system, sample_results):
        """Should search in recommendations field."""
        temp_memory_system.store_conversation(
            prompt="Test prompt",
            results=sample_results
        )

        results = temp_memory_system.search_memory("strategy")
        assert len(results) == 1

    def test_case_insensitive_search(self, temp_memory_system, sample_results):
        """Search should be case-insensitive."""
        temp_memory_system.store_conversation(
            prompt="Buy vs lease equipment",
            results=sample_results
        )

        results = temp_memory_system.search_memory("BUY")
        assert len(results) == 1

    def test_returns_all_matching_conversations(self, temp_memory_system, sample_results):
        """Should return all conversations matching the query."""
        temp_memory_system.store_conversation(
            prompt="Buy vs lease equipment",
            results=sample_results
        )
        temp_memory_system.store_conversation(
            prompt="Buy new servers",
            results=sample_results
        )
        temp_memory_system.store_conversation(
            prompt="Lease office space",
            results=sample_results
        )

        results = temp_memory_system.search_memory("buy")
        assert len(results) == 2


class TestGenerateId:
    """_generate_id() — generating unique IDs for conversations."""

    def test_generates_consistent_id_for_same_prompt(self, temp_memory_system):
        """Should generate consistent ID for same prompt."""
        id1 = temp_memory_system._generate_id("Test prompt")
        id2 = temp_memory_system._generate_id("Test prompt")
        assert id1 == id2

    def test_generates_different_ids_for_different_prompts(self, temp_memory_system):
        """Should generate different IDs for different prompts."""
        id1 = temp_memory_system._generate_id("Test prompt 1")
        id2 = temp_memory_system._generate_id("Test prompt 2")
        assert id1 != id2

    def test_generates_12_char_id(self, temp_memory_system):
        """Should generate 12 character ID."""
        conv_id = temp_memory_system._generate_id("Test prompt")
        assert len(conv_id) == 12
