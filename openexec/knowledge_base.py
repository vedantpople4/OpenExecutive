#!/usr/bin/env python3
"""Custom knowledge base system for OpenExec - RAG over proprietary company data."""

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    """Lowercase word/number tokens, stripping punctuation."""
    return _TOKEN_RE.findall(text.lower())


class KnowledgeBase:
    """Manages custom knowledge base with RAG capabilities."""

    def __init__(self, kb_dir: str = "knowledge_base"):
        self.kb_dir = Path(kb_dir)
        self.kb_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.kb_dir / "documents").mkdir(exist_ok=True)
        (self.kb_dir / "chunks").mkdir(exist_ok=True)
        (self.kb_dir / "index").mkdir(exist_ok=True)

        # Knowledge base index
        self.index_path = self.kb_dir / "kb_index.json"
        self.index = self._load_index()

        # In-memory cache of chunk files, keyed by doc_id, to avoid re-reading
        # the same JSON from disk on every retrieve_relevant() call.
        self._chunk_cache: Dict[str, Dict[str, Any]] = {}

    def _get_chunk_data(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Load a document's chunk data, from the in-memory cache if present."""
        if doc_id in self._chunk_cache:
            return self._chunk_cache[doc_id]
        chunk_path = self.kb_dir / "chunks" / f"{doc_id}.json"
        if not chunk_path.exists():
            return None
        with open(chunk_path, 'r') as f:
            chunk_data = json.load(f)
        self._chunk_cache[doc_id] = chunk_data
        return chunk_data

    def _load_index(self) -> Dict[str, Any]:
        """Load knowledge base index from disk."""
        if self.index_path.exists():
            with open(self.index_path, 'r') as f:
                return json.load(f)
        return {
            "documents": [],
            "categories": {},
            "last_updated": None
        }

    def _save_index(self) -> None:
        """Save knowledge base index to disk."""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_path, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _generate_doc_id(self, filename: str) -> str:
        """Generate a unique ID for a document."""
        return hashlib.md5(filename.encode()).hexdigest()[:12]

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks for better retrieval."""
        chunks = []
        sentences = text.split('. ')

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _upsert_doc(self, doc_metadata: Dict[str, Any], chunk_data: Dict[str, Any]) -> None:
        """Write a document's chunks and register it in the index idempotently.

        Re-ingesting the same doc_id (same filename) replaces the prior entry
        instead of appending a duplicate to documents/categories.
        """
        doc_id = doc_metadata["id"]

        # Drop any prior registration for this doc id.
        for i, doc in enumerate(self.index["documents"]):
            if doc["id"] == doc_id:
                self.index["documents"].pop(i)
                break
        for cat, ids in self.index["categories"].items():
            if doc_id in ids:
                ids.remove(doc_id)
                break
        old_chunk = self.kb_dir / "chunks" / f"{doc_id}.json"
        if old_chunk.exists():
            old_chunk.unlink()
        if doc_id in self._chunk_cache:
            del self._chunk_cache[doc_id]

        # Write new content and register it.
        chunk_path = self.kb_dir / "chunks" / f"{doc_id}.json"
        with open(chunk_path, 'w') as f:
            json.dump(chunk_data, f, indent=2)
        self._chunk_cache[doc_id] = chunk_data

        self.index["documents"].append(doc_metadata)

        category = doc_metadata["category"]
        if category not in self.index["categories"]:
            self.index["categories"][category] = []
        self.index["categories"][category].append(doc_id)

        self._save_index()

    def ingest_document(self, file_path: str, category: str = "general",
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Ingest a document into the knowledge base.

        Args:
            file_path: Path to the document file
            category: Category for the document (financials, pitch_deck, etc.)
            metadata: Additional metadata about the document

        Returns:
            doc_id: Unique ID for the ingested document
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        # Read document content
        content = file_path.read_text()

        # Generate document ID
        doc_id = self._generate_doc_id(file_path.name)

        # Create document metadata
        doc_metadata = {
            "id": doc_id,
            "filename": file_path.name,
            "category": category,
            "ingested_at": datetime.now().isoformat(),
            "size": len(content),
            "metadata": metadata or {}
        }

        # Chunk the document
        chunks = self._chunk_text(content)

        # Save chunks
        chunk_data = {
            "doc_id": doc_id,
            "metadata": doc_metadata,
            "chunks": chunks
        }

        self._upsert_doc(doc_metadata, chunk_data)

        return doc_id

    def ingest_text(self, text: str, category: str = "general",
                   title: str = "Untitled", metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Ingest text directly into the knowledge base.

        Args:
            text: Text content to ingest
            category: Category for the content
            title: Title for the content
            metadata: Additional metadata

        Returns:
            doc_id: Unique ID for the ingested content
        """
        # Generate document ID
        doc_id = self._generate_doc_id(title)

        # Create document metadata
        doc_metadata = {
            "id": doc_id,
            "title": title,
            "category": category,
            "ingested_at": datetime.now().isoformat(),
            "size": len(text),
            "metadata": metadata or {}
        }

        # Chunk the text
        chunks = self._chunk_text(text)

        # Save chunks
        chunk_data = {
            "doc_id": doc_id,
            "metadata": doc_metadata,
            "chunks": chunks
        }

        self._upsert_doc(doc_metadata, chunk_data)

        return doc_id

    def retrieve_relevant(self, query: str, category: Optional[str] = None,
                         limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks based on a query, ranked by TF-IDF cosine
        similarity (pure stdlib -- no numpy/sklearn dependency).

        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of relevant chunks with metadata, "score" in [0, 1]
        """
        query_terms = _tokenize(query)
        if not query_terms:
            return []

        # Get documents to search
        doc_ids = self.index["documents"]
        if category:
            doc_ids = [
                doc for doc in self.index["documents"]
                if doc["category"] == category
            ]

        # Gather every candidate chunk up front so document frequency (df)
        # can be computed across the whole searched set.
        candidates = []  # (chunk_text, tokens, doc, chunk_index)
        for doc in doc_ids:
            chunk_data = self._get_chunk_data(doc["id"])
            if not chunk_data:
                continue
            for i, chunk in enumerate(chunk_data["chunks"]):
                candidates.append((chunk, _tokenize(chunk), doc, i))

        if not candidates:
            return []

        n_chunks = len(candidates)
        df: Counter = Counter()
        for _, tokens, _, _ in candidates:
            df.update(set(tokens))

        def idf(term: str) -> float:
            # Smoothed idf: terms absent from every chunk still get a (high)
            # finite weight instead of dividing by zero.
            return math.log((n_chunks + 1) / (df.get(term, 0) + 1)) + 1

        query_tf = Counter(query_terms)
        query_vec = {t: tf * idf(t) for t, tf in query_tf.items()}
        query_norm = math.sqrt(sum(w * w for w in query_vec.values())) or 1.0

        results = []
        for chunk, tokens, doc, chunk_index in candidates:
            if not tokens:
                continue
            chunk_tf = Counter(tokens)
            chunk_vec = {t: tf * idf(t) for t, tf in chunk_tf.items()}
            chunk_norm = math.sqrt(sum(w * w for w in chunk_vec.values())) or 1.0

            dot = sum(w * chunk_vec.get(t, 0.0) for t, w in query_vec.items())
            score = dot / (query_norm * chunk_norm)

            if score > 0:
                results.append({
                    "chunk": chunk,
                    "score": round(score, 4),
                    "doc_id": doc["id"],
                    "doc_title": doc.get("title", doc.get("filename", "Unknown")),
                    "category": doc["category"],
                    "chunk_index": chunk_index
                })

        # Sort by score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def get_context_for_query(self, query: str, category: Optional[str] = None) -> str:
        """Generate context string for a query from the knowledge base."""
        relevant = self.retrieve_relevant(query, category, limit=3)

        if not relevant:
            return ""

        context_lines = ["## Relevant Company Information\n\n"]

        for i, result in enumerate(relevant, 1):
            context_lines.append(f"### Source {i}: {result['doc_title']}")
            context_lines.append(f"Category: {result['category']}")
            context_lines.append("")
            context_lines.append(result['chunk'])
            context_lines.append("")

        return "\n".join(context_lines)

    def list_documents(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all documents in the knowledge base."""
        if category:
            return [
                doc for doc in self.index["documents"]
                if doc["category"] == category
            ]
        return self.index["documents"]

    def list_categories(self) -> List[str]:
        """List all categories in the knowledge base."""
        return list(self.index["categories"].keys())

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the knowledge base."""
        # Find and remove from index
        doc_to_remove = None
        for doc in self.index["documents"]:
            if doc["id"] == doc_id:
                doc_to_remove = doc
                break

        if not doc_to_remove:
            return False

        # Remove from documents list
        self.index["documents"].remove(doc_to_remove)

        # Remove from category
        category = doc_to_remove["category"]
        if category in self.index["categories"]:
            self.index["categories"][category].remove(doc_id)

        # Delete chunk file
        chunk_path = self.kb_dir / "chunks" / f"{doc_id}.json"
        if chunk_path.exists():
            chunk_path.unlink()

        self._save_index()
        return True

    def get_kb_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        total_chunks = 0
        for doc in self.index["documents"]:
            chunk_path = self.kb_dir / "chunks" / f"{doc['id']}.json"
            if chunk_path.exists():
                with open(chunk_path, 'r') as f:
                    chunk_data = json.load(f)
                    total_chunks += len(chunk_data["chunks"])

        return {
            "total_documents": len(self.index["documents"]),
            "total_chunks": total_chunks,
            "categories": self.list_categories(),
            "last_updated": self.index["last_updated"]
        }


# Global knowledge base instance
knowledge_base = KnowledgeBase()