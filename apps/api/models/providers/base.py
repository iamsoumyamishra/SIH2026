"""Abstract model provider interface.

The agent and router depend on this abstraction, never on a concrete provider.
This is the hard architectural boundary described in AGENTS.md: a future
VLLMProvider (or any provider) can be added without changing the agent.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from models.schemas import (
    EmbeddingRequest,
    EmbeddingResponse,
    GenerationRequest,
    GenerationResponse,
    ModelInfo,
)


class ModelProvider(ABC):
    """Contract every model provider must implement."""

    name: str = "base"

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a completion for the given messages/prompt."""

    @abstractmethod
    async def stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        """Yield incremental text chunks (async iterator)."""
        if False:  # async-generator shape so subclasses type-check as iterators
            yield ""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider backend is reachable."""

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Return model names exposed by the provider backend."""

    @abstractmethod
    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Return embedding vectors."""

    def describe(self) -> ModelInfo:
        """Return static metadata. Overridden by concrete providers when they
        know the model details."""
        return ModelInfo(id=self.name, provider=self.name, model_name=self.name)
