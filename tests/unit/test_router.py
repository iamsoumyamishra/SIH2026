"""Tests for the model router and registry."""
from __future__ import annotations

import pytest

from models.router import ModelRouter, ModelUnavailableError
from models.schemas import ModelInfo, RoutingRequest, TaskKind


class _StubRegistry:
    def __init__(self, models: dict[str, ModelInfo]):
        self._models = models

    def get(self, role: str) -> ModelInfo | None:
        return self._models.get(role)


def _mk(role: str, name: str, **kw) -> ModelInfo:
    base = dict(
        id=role, provider="ollama", model_name=name,
        capabilities=["text"], vision_support=False,
        tool_support=False, embedding_support=False,
    )
    base.update(kw)
    return ModelInfo(**base)


def test_routes_vision_to_vision_model():
    reg = _StubRegistry({
        "general": _mk("general", "g:7b"),
        "vision": _mk("vision", "v:7b", vision_support=True),
    })
    router = ModelRouter(reg)  # type: ignore[arg-type]
    res = router.route(RoutingRequest(task_type=TaskKind.VISION))
    assert res.model_id == "vision"
    assert res.task_kind == TaskKind.VISION


def test_routes_coding_keyword_to_coding_model():
    reg = _StubRegistry({
        "general": _mk("general", "g:7b"),
        "coding": _mk("coding", "c:7b"),
    })
    router = ModelRouter(reg)  # type: ignore[arg-type]
    res = router.route(RoutingRequest(prompt="Write a python program that calculates x"))
    assert res.model_id == "coding"


def test_routes_explicit_coding_type():
    reg = _StubRegistry({
        "general": _mk("general", "g:7b"),
        "coding": _mk("coding", "c:7b"),
    })
    router = ModelRouter(reg)  # type: ignore[arg-type]
    res = router.route(RoutingRequest(task_type=TaskKind.CODING, prompt="sum two numbers"))
    assert res.model_id == "coding"


def test_reasoning_task_selects_reasoning():
    reg = _StubRegistry({
        "general": _mk("general", "g:7b"),
        "reasoning": _mk("reasoning", "r:7b"),
    })
    router = ModelRouter(reg)  # type: ignore[arg-type]
    res = router.route(RoutingRequest(task_type=TaskKind.REASONING))
    assert res.model_id == "reasoning"


def test_default_selects_general():
    reg = _StubRegistry({"general": _mk("general", "g:7b")})
    router = ModelRouter(reg)  # type: ignore[arg-type]
    res = router.route(RoutingRequest(prompt="hello"))
    assert res.model_id == "general"


def test_vision_falls_back_to_reasoning():
    """If no vision model, vision falls back rather than crashing."""
    reg = _StubRegistry({
        "general": _mk("general", "g:7b"),
        "reasoning": _mk("reasoning", "r:7b"),
    })
    router = ModelRouter(reg)  # type: ignore[arg-type]
    res = router.route(RoutingRequest(task_type=TaskKind.VISION))
    assert res.model_id == "reasoning"


def test_raises_when_no_model_configured():
    router = ModelRouter(_StubRegistry({}))  # type: ignore[arg-type]
    with pytest.raises(ModelUnavailableError):
        router.route(RoutingRequest(prompt="hi"))
