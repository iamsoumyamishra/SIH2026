"""Local embeddings via the model provider abstraction.

The embedding model is called through the local Ollama endpoint only. Calls are
synchronous so they can be used from both sync (CLI/tests) and async (API)
contexts without event-loop conflicts. All communication stays local.
"""
from __future__ import annotations

import httpx

from config.settings import settings


class EmbeddingService:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_embedding_model
        self._timeout = 120.0

    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        with httpx.Client(timeout=self._timeout) as client:
            for t in texts:
                resp = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": t},
                )
                resp.raise_for_status()
                vectors.append(resp.json()["embedding"])
        return vectors
