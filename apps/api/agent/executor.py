"""Execution of plan steps.

The executor walks the plan produced by the planner and dispatches each action to
a registered handler. Handlers may call tools (via the ToolRegistry), the model
(via the ModelProvider), or service subsystems (documents, RAG, sandbox,
artifacts) supplied through an execution environment.

This design keeps the agent decoupled from concrete implementations: new actions
are added by registering a handler, and none of them touch Ollama/core services
directly except through the abstractions.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from agent.context import AgentContext
from agent.planner import Plan
from agent.state import AgentState, StateMachine


class ActionHandler:
    """Environment of handlers the executor can dispatch to."""

    def __init__(self) -> None:
        # action_name -> async fn(context, detail) -> Any
        self._handlers: dict[str, Callable[[AgentContext, str], Awaitable[Any]]] = {}

    def register(self, action: str, fn: Callable[[AgentContext, str], Awaitable[Any]]) -> None:
        self._handlers[action] = fn

    def has(self, action: str) -> bool:
        return action in self._handlers

    def get(self, action: str) -> Callable[[AgentContext, str], Awaitable[Any]] | None:
        return self._handlers.get(action)


class Executor:
    def __init__(self, handlers: ActionHandler) -> None:
        self.handlers = handlers

    async def execute_plan(
        self,
        context: AgentContext,
        plan: Plan,
        state: StateMachine,
    ) -> bool:
        """Run each step, tracking results.

        Returns True on overall success (all steps completed with ok results).
        State transitions are managed by the orchestrator, not here.
        """
        results: list[Any] = []
        for step in plan.steps:
            if state.is_terminal():
                break
            action = step["action"]
            detail = step.get("detail", "")
            context.add_step(detail or action)

            if action in ("verify_result", "verify_document"):
                if not state.is_terminal():
                    state.transition(AgentState.VERIFYING)
            elif action in ("generate_code", "execute_code", "run_tests"):
                if not state.is_terminal():
                    state.transition(AgentState.EXECUTING)

            if not self.handlers.has(action):
                context.complete_step(detail or action)
                context.tool_results[action] = {
                    "ok": False,
                    "error": f"Action '{action}' has no handler yet.",
                }
                results.append(None)
                continue

            fn = self.handlers.get(action)
            assert fn is not None  # guarded by handlers.has(action) above
            try:
                result = await fn(context, detail)
                context.tool_results[action] = result
                results.append(result)
            except Exception as exc:  # noqa: BLE001
                context.tool_results[action] = {"ok": False, "error": str(exc)}
                results.append(None)
            context.complete_step(detail or action)

        return all(
            r is not None and (not isinstance(r, dict) or r.get("ok", True)) for r in results
        )
