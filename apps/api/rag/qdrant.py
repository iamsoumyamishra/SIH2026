"""Vector store for RAG.

Two implementations, chosen by settings.rag_backend (see ADR-001):
  - "local": an in-process numpy fallback vector store (no external service)
  - "qdrant": the Qdrant service via the official client

Both are local; neither is a cloud service.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from config.settings import settings


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, points: list[dict[str, Any]]) -> None:
        """points: [{id, vector, payload}]"""

    @abstractmethod
    def search(self, vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        """return [{id, score, payload}]"""

    @abstractmethod
    def count(self) -> int:
        ...


class LocalVectorStore(VectorStore):
    """In-memory vector store using numpy cosine similarity. Quantized to float32."""

    def __init__(self) -> None:
        self._vectors: dict[str, np.ndarray] = {}
        self._payloads: dict[str, dict[str, Any]] = {}

    def upsert(self, points: list[dict[str, Any]]) -> None:
        for p in points:
            pid = p["id"]
            vector = np.asarray(p["vector"], dtype=np.float32)
            self._vectors[pid] = vector
            self._payloads[pid] = p.get("payload", {})

    def search(self, vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        query = np.asarray(vector, dtype=np.float32)
        if not self._vectors:
            return []
        ids = list(self._vectors.keys())
        mat = np.stack([self._vectors[i] for i in ids])
        qn = np.linalg.norm(query)
        if qn == 0:
            return []
        sims = mat @ query / (np.linalg.norm(mat, axis=1) * qn)
        order = np.argsort(sims)[::-1][:limit]
        results = []
        for idx in order:
            pid = ids[int(idx)]
            results.append(
                {
                    "id": pid,
                    "score": round(float(sims[int(idx)]), 6),
                    "payload": self._payloads[pid],
                }
            )
        return results

    def count(self) -> int:
        return len(self._vectors)


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        url: str | None = None,
        collection: str | None = None,
        dim: int | None = None,
    ) -> None:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models

        self._models = models
        self._url = url or settings.qdrant_url
        self._collection = collection or settings.qdrant_collection
        self._dim = dim or settings.embedding_dim
        self._client = QdrantClient(url=self._url)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        collections = [c.name for c in self._client.get_collections().collections]
        if self._collection not in collections:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=self._models.VectorParams(
                    size=self._dim, distance=self._models.Distance.COSINE
                ),
            )

    def upsert(self, points: list[dict[str, Any]]) -> None:
        pts = []
        for p in points:
            pts.append(
                self._models.PointStruct(
                    id=p.get("id", str(uuid.uuid4())),
                    vector=p["vector"],
                    payload=p.get("payload", {}),
                )
            )
        self._client.upsert(collection_name=self._collection, points=pts)

    def search(self, vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        hits = self._client.search(
            collection_name=self._collection, query_vector=vector, limit=limit
        )
        return [
            {"id": h.id, "score": h.score, "payload": h.payload or {}} for h in hits
        ]

    def count(self) -> int:
        return int(self._client.count(collection_name=self._collection).count)


def get_vector_store() -> VectorStore:
    if settings.rag_backend == "qdrant":
        try:
            return QdrantVectorStore()
        except Exception:  # noqa: BLE001
            # Degrade to local store but keep it explicit and local.
            return LocalVectorStore()
    return LocalVectorStore()


_vector_store: VectorStore | None = None


def vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = get_vector_store()
    return _vector_store


def reset_vector_store() -> None:
    global _vector_store
    _vector_store = None
