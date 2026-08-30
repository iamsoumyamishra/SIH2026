"""RAG retrieval: embed query → search store → return chunks with metadata."""

from __future__ import annotations

from typing import Any

from rag.embeddings import EmbeddingService
from rag.qdrant import VectorStore, vector_store


class RetrievalService:
    def __init__(
        self,
        embeddings: EmbeddingService | None = None,
        store: VectorStore | None = None,
    ) -> None:
        self.embeddings = embeddings or EmbeddingService()
        self.store = store or vector_store()

    def search(self, query: str, limit: int = 5, min_score: float = 0.0) -> dict[str, Any]:
        vector = self.embeddings.embed(query)
        hits = self.store.search(vector, limit=limit)
        results = []
        for h in hits:
            payload = h["payload"]
            if h["score"] < min_score:
                continue
            results.append(
                {
                    "document_id": payload.get("document_id"),
                    "document_name": payload.get("document_name"),
                    "page_number": payload.get("page_number"),
                    "section": payload.get("section"),
                    "version": payload.get("version"),
                    "classification": payload.get("classification"),
                    "chunk_id": payload.get("chunk_id"),
                    "text": payload.get("text", ""),
                    "score": h["score"],
                }
            )
        return {"query": query, "results": results, "count": len(results)}
