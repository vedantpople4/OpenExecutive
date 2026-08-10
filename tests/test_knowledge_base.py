"""Tests for openexec/knowledge_base.py — idempotent ingestion and retrieval."""

import pytest

from openexec.knowledge_base import KnowledgeBase


@pytest.fixture
def kb(tmp_path):
    return KnowledgeBase(kb_dir=str(tmp_path / "kb"))


def _write_sample(path, text="Company revenue: $5M ARR."):
    path.write_text(text)
    return str(path)


class TestIdempotentIngest:
    def test_reingest_same_file_replaces_entry(self, kb, tmp_path):
        doc = _write_sample(tmp_path / "a.md")
        first = kb.ingest_document(doc, "financials")
        kb.ingest_document(doc, "financials")

        assert len(kb.list_documents()) == 1
        assert len(kb.index["categories"]["financials"]) == 1
        assert first in kb.index["categories"]["financials"]

    def test_reingest_updated_content_visible(self, kb, tmp_path):
        doc = tmp_path / "a.md"
        _write_sample(doc, "Old content.")
        kb.ingest_document(str(doc), "financials")
        _write_sample(doc, "New content mentions ARR growth.")
        kb.ingest_document(str(doc), "financials")

        results = kb.retrieve_relevant("arr", limit=5)
        assert any("arr" in r["chunk"].lower() for r in results)

    def test_get_kb_stats_counts_once(self, kb, tmp_path):
        doc = _write_sample(tmp_path / "a.md")
        kb.ingest_document(doc, "general")
        before = kb.get_kb_stats()["total_documents"]
        kb.ingest_document(doc, "general")
        after = kb.get_kb_stats()["total_documents"]
        assert before == 1
        assert after == 1


class TestRetrieve:
    def test_retrieves_relevant_chunk(self, kb, tmp_path):
        _write_sample(tmp_path / "fin.md", "Our revenue grew to $5M ARR in Q2.")
        kb.ingest_document(str(tmp_path / "fin.md"), "financials")
        results = kb.retrieve_relevant("revenue")
        assert results
        assert results[0]["score"] > 0

    def test_empty_query_returns_empty(self, kb, tmp_path):
        _write_sample(tmp_path / "fin.md", "Something here.")
        kb.ingest_document(str(tmp_path / "fin.md"), "general")
        assert kb.retrieve_relevant("") == []