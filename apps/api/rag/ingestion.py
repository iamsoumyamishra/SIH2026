"""RAG ingestion: parse → chunk → embed → store (all local)."""

from __future__ import annotations

from typing import Any

from rag.chunking import chunk_text
from rag.embeddings import EmbeddingService
from rag.qdrant import VectorStore, vector_store


class IngestionService:
    def __init__(
        self,
        embeddings: EmbeddingService | None = None,
        store: VectorStore | None = None,
    ) -> None:
        self.embeddings = embeddings or EmbeddingService()
        self.store = store or vector_store()

    def ingest_text(
        self,
        text: str,
        document_id: str,
        document_name: str = "",
        page_number: int | None = None,
        section: str | None = None,
        version: str | None = None,
        classification: str | None = None,
    ) -> dict[str, Any]:
        chunks = chunk_text(text, document_id, document_name, page_number, section)
        if not chunks:
            return {"document_id": document_id, "chunks_indexed": 0}

        texts = [c.text for c in chunks]
        vectors = self.embeddings.embed_many(texts)

        points: list[dict[str, Any]] = []
        for chunk, vector in zip(chunks, vectors):
            points.append(
                {
                    "id": chunk.chunk_id,
                    "vector": vector,
                    "payload": {
                        **chunk.meta,
                        "chunk_id": chunk.chunk_id,
                        "version": version,
                        "classification": classification,
                        "text": chunk.text,
                    },
                }
            )

        self.store.upsert(points)
        return {
            "document_id": document_id,
            "chunks_indexed": len(points),
            "store_count": self.store.count(),
        }

    def clear(self) -> None:
        if hasattr(self.store, "_vectors"):
            self.store._vectors.clear()  # type: ignore[attr-defined]
            self.store._payloads.clear()  # type: ignore[attr-defined]
