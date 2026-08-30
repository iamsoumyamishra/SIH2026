"""Ollama model provider.

Communicates with the LOCAL Ollama instance only. All inference, embeddings,
and model listing happen against http://localhost:11434 (OLLAMA_BASE_URL).
No data ever leaves the machine.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from config.settings import settings
from models.providers.base import ModelProvider
from models.schemas import (
    EmbeddingRequest,
    EmbeddingResponse,
    GenerationRequest,
    GenerationResponse,
)


class OllamaProvider(ModelProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._timeout = timeout

    # ── helpers ──────────────────────────────────────────────
    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self.base_url}{path}", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def _get(self, path: str) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"{self.base_url}{path}")
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _prepare_messages(req: GenerationRequest) -> list[dict[str, Any]]:
        messages = list(req.messages)
        if req.system:
            messages.insert(0, {"role": "system", "content": req.system})
        elif req.prompt is not None and not messages:
            messages.append({"role": "user", "content": req.prompt})
        # Add vision images to the last user message if provided.
        messages = _attach_images(messages, req.images)
        return messages

    # ── interface ────────────────────────────────────────────
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": self._prepare_messages(request),
            "stream": False,
        }
        if request.temperature is not None:
            payload["options"] = {"temperature": request.temperature}
        if request.max_tokens is not None:
            payload["options"] = {
                **(payload.get("options") or {}),
                "num_predict": request.max_tokens,
            }
        if request.tools is not None:
            payload["tools"] = request.tools

        data = await self._post("/api/chat", payload)
        text = data.get("message", {}).get("content", "")
        tool_calls = data.get("message", {}).get("tool_calls")
        done_reason = data.get("done_reason")
        return GenerationResponse(
            text=text,
            model=request.model,
            finish_reason=done_reason,
            tool_calls=[dict(tc) for tc in tool_calls] if tool_calls else None,
            usage={"prompt": data.get("prompt_eval_count"), "completion": data.get("eval_count")},
        )

    async def stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": self._prepare_messages(request),
            "stream": True,
        }
        if request.temperature is not None:
            payload["options"] = {"temperature": request.temperature}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except Exception:
                        continue
                    delta = chunk.get("message", {}).get("content")
                    if delta:
                        yield delta

    async def health_check(self) -> bool:
        try:
            await self._get("/api/tags")
            return True
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        data = await self._get("/api/tags")
        return [m["name"] for m in data.get("models", [])]

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        texts = request.texts or ([request.text] if request.text else [])
        model = request.model or settings.ollama_embedding_model
        payload: dict[str, Any] = {"model": model}
        vectors: list[list[float]] = []
        for t in texts:
            payload["prompt"] = t
            data = await self._post("/api/embeddings", payload)
            vectors.append(data["embedding"])
        dim = len(vectors[0]) if vectors else 0
        return EmbeddingResponse(vectors=vectors, model=model, dim=dim)


def _attach_images(
    messages: list[dict[str, Any]], images: list[str] | None
) -> list[dict[str, Any]]:
    """Attach base64 image data to the last user message.

    Accepts base64 strings or existing 'images' lists already present.
    """
    if not images:
        return messages
    # find last user message
    for msg in reversed(messages):
        if msg.get("role") == "user":
            existing = msg.get("images") or []
            msg["images"] = existing + list(images)
            return messages
    messages.append({"role": "user", "content": "", "images": list(images)})
    return messages
