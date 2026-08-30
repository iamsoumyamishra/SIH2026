"""Deterministic, rule-based model router.

Maps a task (type, capabilities, vision, etc.) to the best configured model.
No ML is involved — this is intentionally simple per AGENTS.md §9.
"""
from __future__ import annotations

from models.registry import ModelRegistry
from models.schemas import RoutingRequest, RoutingResult, TaskKind


class ModelRouter:
    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self.registry = registry or ModelRegistry()

    def route(self, request: RoutingRequest) -> RoutingResult:
        """Choose a model for the given routing request."""
        # Explicit capability requirements
        if request.requires_vision or request.task_type == TaskKind.VISION:
            return self._select(
                "vision",
                fallback=["reasoning", "general"],
                reason="Vision task → vision model",
                kind=TaskKind.VISION,
            )

        code_keywords = (
            "python", "code", "program", "script", "function", "algorithm",
            "calculate the required values", "write a program", "implement",
        )
        if request.task_type == TaskKind.CODING or (
            request.prompt and _has_any(request.prompt, code_keywords)
        ):
            return self._select(
                "coding",
                fallback=["reasoning", "general"],
                reason="Coding/tool task → coding model",
                kind=TaskKind.CODING,
            )

        if request.task_type == TaskKind.REASONING:
            return self._select(
                "reasoning",
                fallback=["general"],
                reason="Complex reasoning → reasoning model",
                kind=TaskKind.REASONING,
            )

        if request.task_type == TaskKind.DOCUMENT:
            return self._select(
                "reasoning",
                fallback=["general"],
                reason="Document task → reasoning model",
                kind=TaskKind.DOCUMENT,
            )

        return self._select(
            "general",
            fallback=["reasoning"],
            reason="Default → general model",
            kind=TaskKind.GENERAL,
        )

    def _select(
        self,
        preferred: str,
        fallback: list[str],
        reason: str,
        kind: TaskKind,
    ) -> RoutingResult:
        for role in [preferred, *fallback]:
            info = self.registry.get(role)
            if info is not None:
                return RoutingResult(
                    model_id=info.id,
                    model_name=info.model_name,
                    provider=info.provider,
                    reason=reason,
                    task_kind=kind,
                )
        raise ModelUnavailableError(
            "No configured model available. Pull a general model and set "
            "OLLAMA_GENERAL_MODEL (see README → Ollama Setup)."
        )


class ModelUnavailableError(Exception):
    pass


def _has_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(k in lowered for k in keywords)
