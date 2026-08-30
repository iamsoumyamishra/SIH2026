"""Agent-run endpoints (AGENTS.md §29: agents).

Reports persisted runs, per-step progress, tool executions, and artifacts.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.models import AgentRun
from db.session import get_db
from security import auth

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/runs")
def list_runs(
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    runs = db.query(AgentRun).order_by(AgentRun.id.desc()).limit(50).all()
    return [
        {
            "id": r.id,
            "task_id": r.task_id,
            "status": r.status.value if r.status else None,
            "model_calls": r.model_calls,
            "started_at": r.started_at.isoformat() if r.started_at else None,
        }
        for r in runs
    ]


@router.get("/runs/{run_id}")
def run_detail(
    run_id: int,
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": run.id,
        "task_id": run.task_id,
        "status": run.status.value if run.status else None,
        "model_calls": run.model_calls,
        "selected_models": run.selected_models,
        "verification_result": run.verification_result,
        "steps": [
            {
                "id": s.id,
                "label": s.label,
                "detail": s.detail,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
            }
            for s in run.steps
        ],
        "tools": [
            {
                "tool_name": t.tool_name,
                "status": t.status.value if t.status else None,
                "risk_level": t.risk_level,
                "duration_ms": t.duration_ms,
            }
            for t in run.tool_executions
        ],
        "artifacts": [
            {
                "name": a.name,
                "kind": a.kind,
                "id": a.id,
                "verification_status": (
                    a.verification_status.value if a.verification_status else None
                ),
            }
            for a in run.artifacts
        ],
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }
