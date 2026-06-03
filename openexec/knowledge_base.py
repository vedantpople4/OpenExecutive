#!/usr/bin/env python3
"""Custom knowledge base system for OpenExec - RAG over proprietary company data."""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import hashlib


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

        chunk_path = self.kb_dir / "chunks" / f"{doc_id}.json"
        with open(chunk_path, 'w') as f:
            json.dump(chunk_data, f, indent=2)

        # Update index
        self.index["documents"].append(doc_metadata)

        # Update category index
        if category not in self.index["categories"]:
            self.index["categories"][category] = []
        self.index["categories"][category].append(doc_id)

        self._save_index()

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

        chunk_path = self.kb_dir / "chunks" / f"{doc_id}.json"
        with open(chunk_path, 'w') as f:
            json.dump(chunk_data, f, indent=2)

        # Update index
        self.index["documents"].append(doc_metadata)

        # Update category index
        if category not in self.index["categories"]:
            self.index["categories"][category] = []
        self.index["categories"][category].append(doc_id)

        self._save_index()

        return doc_id

    def retrieve_relevant(self, query: str, category: Optional[str] = None,
                         limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks based on a query.

        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of relevant chunks with metadata
        """
        query_lower = query.lower()
        query_keywords = set(query_lower.split())

        results = []

        # Get documents to search
        doc_ids = self.index["documents"]
        if category:
            doc_ids = [
                doc for doc in self.index["documents"]
                if doc["category"] == category
            ]

        # Search through chunks
        for doc in doc_ids:
            chunk_path = self.kb_dir / "chunks" / f"{doc['id']}.json"
            if not chunk_path.exists():
                continue

            with open(chunk_path, 'r') as f:
                chunk_data = json.load(f)

            # Score each chunk
            for i, chunk in enumerate(chunk_data["chunks"]):
                chunk_lower = chunk.lower()

                # Calculate relevance score
                score = 0
                for keyword in query_keywords:
                    if keyword in chunk_lower:
                        score += 1

                if score > 0:
                    results.append({
                        "chunk": chunk,
                        "score": score,
                        "doc_id": doc["id"],
                        "doc_title": doc.get("title", doc.get("filename", "Unknown")),
                        "category": doc["category"],
                        "chunk_index": i
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