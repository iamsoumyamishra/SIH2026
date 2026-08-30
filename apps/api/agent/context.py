"""Agent context: the shared state container passed through a run.

Holds immutable task inputs plus mutable execution artifacts (steps, selected
model, tool results, documents, artifacts) that the orchestrator/progress
streaming layer consumes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepRecord:
    label: str
    status: str = "running"
    detail: str | None = None
    model: str | None = None


@dataclass
class AgentContext:
    task_id: int | None = None
    user_id: int | None = None
    prompt: str = ""
    workspace: str | None = None
    workspace_obj: Any = None  # bound Workspace instance (set by caller)

    task_type: str = "unknown"
    selected_model_id: str | None = None
    selected_model_name: str | None = None
    selected_provider: str | None = None
    model_reason: str | None = None

    steps: list[StepRecord] = field(default_factory=list)
    tool_results: dict[str, Any] = field(default_factory=dict)
    documents_accessed: list[str] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    retrieved_sources: list[dict[str, Any]] = field(default_factory=list)
    verification: dict[str, Any] = field(default_factory=dict)

    # Sovereignty / observability counters
    model_calls: int = 0
    tool_executions: int = 0

    def add_step(self, label: str, detail: str | None = None) -> StepRecord:
        step = StepRecord(label=label, detail=detail, model=self.selected_model_name)
        self.steps.append(step)
        return step

    def complete_step(self, label: str) -> None:
        for step in self.steps:
            if step.label == label and step.status == "running":
                step.status = "done"
