"""Agent orchestrator: the top-level coordinator for a task run.

Orchestrates: classify → plan → route model → execute → verify, within a bounded
iteration loop (MAX_AGENT_ITERATIONS). Only the abstractions (ModelRouter,
ModelProvider, ToolRegistry, handlers) are used — never Ollama directly.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from agent.context import AgentContext
from agent.executor import ActionHandler, Executor
from agent.planner import Planner
from agent.state import AgentState, IllegalTransitionError, StateMachine
from agent.verifier import Verifier
from config.settings import settings
from models.registry import ModelRegistry
from models.router import ModelRouter, ModelUnavailableError
from models.schemas import RoutingRequest

# Progress stream semantics used by the UI / SSE layer.
ProgressCallback = Callable[[str, str, str | None], Awaitable[None]]  # (label, status, detail)


class Orchestrator:
    def __init__(
        self,
        planner: Planner | None = None,
        router: ModelRouter | None = None,
        registry: ModelRegistry | None = None,
        verifier: Verifier | None = None,
        handlers: ActionHandler | None = None,
        max_iterations: int | None = None,
    ) -> None:
        self.planner = planner or Planner()
        self.registry = registry or ModelRegistry()
        self.router = router or ModelRouter(self.registry)
        self.verifier = verifier or Verifier()
        self.handlers = handlers or ActionHandler()
        self.executor = Executor(self.handlers)
        self.max_iterations = max_iterations or settings.max_agent_iterations
        self.on_progress: ProgressCallback | None = None

    async def _emit(self, label: str, status: str, detail: str | None = None) -> None:
        if self.on_progress:
            try:
                await self.on_progress(label, status, detail)
            except Exception:
                pass

    async def run(self, context: AgentContext, prompt: str) -> AgentContext:
        state = StateMachine(AgentState.RECEIVED)
        context.prompt = prompt

        await self._emit("Task received", "done")
        state.transition(AgentState.CLASSIFYING)
        await self._emit("Classifying task", "done")

        # Plan
        plan = self.planner.plan(prompt)
        context.task_type = plan.task_type
        state.transition(AgentState.PLANNING)
        await self._emit("Planning", "done", f"task={plan.task_type}")

        # Route model
        try:
            routed = self.router.route(
                RoutingRequest(
                    task_type=_task_kind(plan.task_type),
                    prompt=prompt,
                    requires_vision=plan.requires_vision,
                    requires_tool_calling=plan.requires_tool_calling,
                )
            )
            context.selected_model_id = routed.model_id
            context.selected_model_name = routed.model_name
            context.selected_provider = routed.provider
            context.model_reason = routed.reason
            await self._emit(
                "Selecting model",
                "done",
                f"{routed.model_name} ({routed.provider})",
            )
        except ModelUnavailableError as exc:
            # Degrade gracefully: continue the (possibly deterministic) plan.
            context.model_reason = str(exc)
            context.steps.append(_step_done(f"Model unavailable: {exc}"))
            await self._emit("Model unavailable", "warning", str(exc))

        # Bounded execution loop
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            await self._emit("Executing plan", "running", f"iteration {iteration}")

            if state.state in (AgentState.COMPLETED, AgentState.FAILED):
                break

            # Try to transition into EXECUTING (may already be there).
            try:
                if not state.is_terminal():
                    state.transition(AgentState.EXECUTING)
            except IllegalTransitionError:
                pass

            ok = await self.executor.execute_plan(context, plan, state)

            if ok:
                state.transition(AgentState.VERIFYING)
                verification = self._verify(context)
                context.verification = verification
                if verification.get("passed", False) or not plan.requires_vision:
                    state.transition(AgentState.COMPLETED)
                    await self._emit("Completed", "done")
                    break
                state.transition(AgentState.OBSERVING)
                await self._emit("Verification failed, re-observing", "running")
            else:
                state.transition(AgentState.OBSERVING)
                await self._emit("Step failed, retrying", "running")

        if state.state != AgentState.COMPLETED:
            if not state.is_terminal():
                try:
                    state.transition(AgentState.FAILED)
                except IllegalTransitionError:
                    pass
            context.verification = {
                "passed": False,
                "items": [{"type": "iteration_budget", "passed": False,
                           "detail": "max iterations reached or plan step failed"}],
            }
            await self._emit("FAILED", "failed", "Max iterations reached or step failure")
        return context

    # ── verification ─────────────────────────────────────────
    def _verify(self, context: AgentContext) -> dict:
        checks: dict = {"passed": True, "items": []}
        docx_paths = [a["path"] for a in context.artifacts if a.get("kind") == "docx"]
        for path in docx_paths:
            res = self.verifier.verify_docx_file(
                path,
                required_paragraphs=context.verification.get("required_paragraphs"),
                required_fields=context.verification.get("required_fields"),
            )
            checks["items"].append(res.to_dict())
            if not res.passed:
                checks["passed"] = False
        if not docx_paths and context.task_type in ("document", "multimodal"):
            # artifact not required for pure analysis
            pass
        return checks


def _task_kind(task_type: str):
    from models.schemas import TaskKind

    mapping = {
        "code": TaskKind.CODING,
        "multimodal": TaskKind.VISION,
        "document": TaskKind.DOCUMENT,
        "general": TaskKind.GENERAL,
    }
    return mapping.get(task_type, TaskKind.GENERAL)


def _step_done(label: str):
    from agent.context import StepRecord

    return StepRecord(label=label, status="done")
