"""Tests for openexec/research.py — web/KB blending and per-process caching."""

from unittest.mock import patch

import pytest

import openexec.research as research


@pytest.fixture(autouse=True)
def clear_cache():
    research._cache.clear()
    yield
    research._cache.clear()


class TestBuildResearchContext:
    def test_disabled_returns_empty(self):
        block, meta = research.build_research_context("q", {"enabled": False})
        assert block == ""
        assert meta == {}

    def test_zero_weights_returns_empty(self):
        block, meta = research.build_research_context("q", {
            "enabled": True, "web_search_weight": 0, "knowledge_base_weight": 0,
        })
        assert block == ""
        assert meta == {}

    def test_web_only_blend(self):
        cfg = {"enabled": True, "web_search_weight": 1.0,
               "knowledge_base_weight": 0.0, "max_context_chars": 3000}
        with patch("openexec.research.web_search") as mock_ws, \
             patch("openexec.research.knowledge_base") as mock_kb:
            mock_ws.return_value = [{"title": "T", "url": "http://x", "content": "c"}]
            block, meta = research.build_research_context("q", cfg)
        assert "Live Web Search" in block
        assert "http://x" in block
        assert "Knowledge Base" not in block
        assert meta["research_sources"] == ["http://x"]
        mock_kb.retrieve_relevant.assert_not_called()

    def test_kb_only_blend(self):
        cfg = {"enabled": True, "web_search_weight": 0.0,
               "knowledge_base_weight": 1.0, "max_context_chars": 3000}
        with patch("openexec.research.web_search") as mock_ws, \
             patch("openexec.research.knowledge_base") as mock_kb:
            mock_kb.retrieve_relevant.return_value = [
                {"doc_title": "doc.md", "chunk": "revenue is strong"}
            ]
            block, meta = research.build_research_context("q", cfg)
        assert "Knowledge Base" in block
        assert "doc.md" in block
        mock_ws.assert_not_called()

    def test_both_empty_returns_empty(self):
        cfg = {"enabled": True, "web_search_weight": 0.5,
               "knowledge_base_weight": 0.5, "max_context_chars": 3000}
        with patch("openexec.research.web_search", return_value=[]), \
             patch("openexec.research.knowledge_base") as mock_kb:
            mock_kb.retrieve_relevant.return_value = []
            block, meta = research.build_research_context("q", cfg)
        assert block == ""
        assert meta == {}

    def test_cache_avoids_second_fetch(self):
        cfg = {"enabled": True, "web_search_weight": 1.0,
               "knowledge_base_weight": 0.0, "max_context_chars": 3000}
        with patch("openexec.research.web_search") as mock_ws:
            mock_ws.return_value = [{"title": "T", "url": "http://x", "content": "c"}]
            research.build_research_context("same q", cfg)
            research.build_research_context("same q", cfg)
        mock_ws.assert_called_once()

    def test_cache_key_includes_weights(self):
        cfg_a = {"enabled": True, "web_search_weight": 1.0,
                 "knowledge_base_weight": 0.0, "max_context_chars": 3000}
        cfg_b = {"enabled": True, "web_search_weight": 0.5,
                 "knowledge_base_weight": 0.5, "max_context_chars": 3000}
        with patch("openexec.research.web_search") as mock_ws, \
             patch("openexec.research.knowledge_base.retrieve_relevant", return_value=[]):
            research.build_research_context("q", cfg_a)
            research.build_research_context("q", cfg_b)
        assert mock_ws.call_count == 2  # different weight keys -> separate fetch