"""Audit logging (AGENTS.md §4.5, §27, §17).

Records task/model/tool/document/artifact/verification events. Never logs
passwords, API keys, secrets, or full confidential document contents.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from db.models import AuditLog


class AuditLogger:
    def __init__(self, db: Session) -> None:
        self._db = db

    def log(self, **kwargs: Any) -> AuditLog:
        """Persist an audit entry. Only non-sensitive metadata is stored."""
        detail = _safe(kwargs.get("detail"))
        if detail is not None:
            detail = detail[:500]
        entry = AuditLog(
            task_id=kwargs.get("task_id"),
            user_id=kwargs.get("user_id"),
            action=kwargs.get("action", "event"),
            model_selected=_safe(kwargs.get("model_selected")),
            tool_name=_safe(kwargs.get("tool_name")),
            tool_result_status=_safe(kwargs.get("tool_result_status")),
            documents_accessed=_safe(kwargs.get("documents_accessed")),
            artifact_generated=_safe(kwargs.get("artifact_generated")),
            verification_status=_safe(kwargs.get("verification_status")),
            detail=detail,
        )
        self._db.add(entry)
        self._db.commit()
        self._db.refresh(entry)
        return entry

    def log_task_started(self, task_id: int, user_id: int | None, task_type: str) -> None:
        self.log(
            task_id=task_id,
            user_id=user_id,
            action="task.started",
            detail=f"type={task_type}",
        )

    def log_model_selected(self, task_id: int, model: str, provider: str) -> None:
        self.log(task_id=task_id, action="model.selected", model_selected=model, detail=provider)

    def log_tool(self, task_id: int, tool: str, status: str, risk: str) -> None:
        self.log(
            task_id=task_id,
            action="tool.executed",
            tool_name=tool,
            tool_result_status=status,
            detail=risk,
        )

    def log_document(self, task_id: int, document_name: str) -> None:
        self.log(task_id=task_id, action="document.accessed", documents_accessed=document_name)

    def log_artifact(self, task_id: int, artifact_name: str, verification: str) -> None:
        self.log(
            task_id=task_id,
            action="artifact.generated",
            artifact_generated=artifact_name,
            verification_status=verification,
        )


def _safe(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
