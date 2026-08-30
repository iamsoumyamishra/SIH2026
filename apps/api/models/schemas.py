"""Pydantic schemas for models, capabilities, and routing."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Capability(StrEnum):
    TEXT = "text"
    REASONING = "reasoning"
    CODING = "coding"
    TOOL_CALLING = "tool_calling"
    VISION = "vision"
    IMAGE = "image"
    EMBEDDING = "embedding"


class ModelInfo(BaseModel):
    """A registered model known to the workbench."""

    id: str
    provider: str
    model_name: str
    capabilities: list[str] = Field(default_factory=list)
    context_length: int | None = None
    vision_support: bool = False
    tool_support: bool = False
    embedding_support: bool = False
    enabled: bool = True


class ModelAvailability(BaseModel):
    """A model plus whether it is actually available at the provider."""

    info: ModelInfo
    available: bool
    error: str | None = None


class TaskKind(StrEnum):
    GENERAL = "general"
    REASONING = "reasoning"
    CODING = "coding"
    VISION = "vision"
    DOCUMENT = "document"
    EMBEDDING = "embedding"


class RoutingRequest(BaseModel):
    """Input to the model router."""

    task_type: TaskKind = TaskKind.GENERAL
    prompt: str = ""
    requires_tool_calling: bool = False
    requires_vision: bool = False
    context_tokens: int = 0


class RoutingResult(BaseModel):
    """A selected model from the router."""

    model_id: str
    model_name: str
    provider: str
    reason: str
    task_kind: TaskKind


class GenerationRequest(BaseModel):
    """A request to a model provider for text generation."""

    model: str
    messages: list[dict[str, str]] = Field(default_factory=list)
    prompt: str | None = None
    system: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    tools: list[dict[str, Any]] | None = None
    images: list[str] | None = None  # base64 or file paths for vision


class GenerationResponse(BaseModel):
    """A text generation result."""

    text: str
    model: str
    finish_reason: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    usage: dict[str, Any] | None = None


class EmbeddingRequest(BaseModel):
    text: str = ""
    texts: list[str] | None = None
    model: str | None = None


class EmbeddingResponse(BaseModel):
    vectors: list[list[float]]
    model: str
    dim: int
