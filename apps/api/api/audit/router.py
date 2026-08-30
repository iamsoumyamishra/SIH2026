"""Audit log endpoints (AGENTS.md §29: audit, §27).

Returns audit trails by task or user with a safe, non-sensitive projection.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.models import AuditLog
from db.session import get_db
from security import auth

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _project(e: AuditLog) -> dict:
    return {
        "id": e.id,
        "task_id": e.task_id,
        "user_id": e.user_id,
        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        "action": e.action,
        "model_selected": e.model_selected,
        "tool_name": e.tool_name,
        "tool_result_status": e.tool_result_status,
        "documents_accessed": e.documents_accessed,
        "artifact_generated": e.artifact_generated,
        "verification_status": e.verification_status,
    }


@router.get("")
def list_audit(
    task_id: int | None = Query(None),
    limit: int = Query(100, le=500),
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = db.query(AuditLog).order_by(AuditLog.id.desc())
    if task_id is not None:
        q = q.filter(AuditLog.task_id == task_id)
    rows = q.limit(limit).all()
    return [_project(e) for e in rows]
