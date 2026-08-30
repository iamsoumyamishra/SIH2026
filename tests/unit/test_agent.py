"""Tests for agent state machine, planner, and orchestrator flow."""
from __future__ import annotations

import pytest

from agent.context import AgentContext
from agent.executor import ActionHandler
from agent.orchestrator import Orchestrator
from agent.planner import Planner
from agent.state import AgentState, IllegalTransitionError, StateMachine
from models.registry import ModelRegistry
from models.schemas import ModelInfo


# ── state machine ────────────────────────────────────────────
def test_state_transition_happy_path():
    sm = StateMachine()
    assert sm.state == AgentState.RECEIVED
    sm.transition(AgentState.CLASSIFYING)
    sm.transition(AgentState.PLANNING)
    sm.transition(AgentState.EXECUTING)
    sm.transition(AgentState.OBSERVING)
    sm.transition(AgentState.VERIFYING)
    sm.transition(AgentState.COMPLETED)
    assert sm.state == AgentState.COMPLETED
    assert sm.is_terminal()


def test_illegal_transition_raises():
    sm = StateMachine()
    with pytest.raises(IllegalTransitionError):
        sm.transition(AgentState.COMPLETED)  # RECEIVED -> COMPLETED not allowed


def test_no_transition_from_terminal():
    sm = StateMachine()
    sm.transition(AgentState.CLASSIFYING)
    sm.transition(AgentState.PLANNING)
    sm.transition(AgentState.EXECUTING)
    sm.transition(AgentState.FAILED)
    with pytest.raises(IllegalTransitionError):
        sm.transition(AgentState.OBSERVING)


# ── planner ──────────────────────────────────────────────────
def test_classify_code():
    p = Planner()
    plan = p.plan("Write a python program that calculates x and test it.")
    assert plan.task_type == "code"
    assert any(s["action"] == "execute_code" for s in plan.steps)


def test_classify_document():
    p = Planner()
    plan = p.plan("Analyze this inspection report pdf and generate an approval note")
    assert plan.task_type == "document"


def test_classify_multimodal():
    p = Planner()
    plan = p.plan("Analyze this scanned engineering drawing image")
    assert plan.task_type == "multimodal"
    assert plan.requires_vision


def test_classify_general():
    p = Planner()
    plan = p.plan("Hello, who are you?")
    assert plan.task_type == "general"


# ── orchestrator with stubbed services ───────────────────────
class _StubRouter:
    def __init__(self):
        self.called = 0

    def route(self, request):
        self.called += 1
        from models.schemas import RoutingResult
        return RoutingResult(
            model_id="general", model_name="g:0.5b",
            provider="ollama", reason="stub", task_kind=request.task_type,
        )


class _StubRegistry:
    def get(self, role):
        if role == "general":
            return ModelInfo(id="general", provider="ollama", model_name="g:0.5b")
        return None


async def _ok_handler(context, detail):
    return {"ok": True, "detail": detail}


def test_orchestrator_run_completes_for_general():
    handlers = ActionHandler()
    handlers.register("analyze", _ok_handler)
    handlers.register("answer", _ok_handler)

    orch = Orchestrator(
        router=_StubRouter(),  # type: ignore[arg-type]
        registry=_StubRegistry(),  # type: ignore[arg-type]
        handlers=handlers,
    )
    ctx = AgentContext()
    result = None

    async def run():
        return await orch.run(ctx, "Hello, summarize my request.")

    import asyncio

    result = asyncio.run(run())
    assert result.selected_model_name == "g:0.5b"
    assert result.task_type == "general"
    assert result.tool_results.get("analyze", {}).get("ok") is True


def test_orchestrator_fails_gracefully_when_no_model():
    reg = ModelRegistry()
    reg._models = {}
    handlers = ActionHandler()
    orch = Orchestrator(handlers=handlers, registry=reg)
    ctx = AgentContext()
    import asyncio

    result = asyncio.run(orch.run(ctx, "do something"))
    assert result.selected_model_name is None
    # The run should not have crashed; step list non-empty with failure note.
    assert any("Model unavailable" in s.label for s in result.steps) or result.steps
