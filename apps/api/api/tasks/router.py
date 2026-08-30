"""Task endpoints: submit + background run, list, detail, cancel, SSE progress.

See AGENTS.md §29 (tasks, agents) and §30 (SSE live agent progress).
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config.settings import BASE_DIR, settings
from db.models import Task, TaskStatus
from db.session import get_db
from security import auth
from services.event_bus import get_event_bus
from services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _upload_dir() -> Path:
    base = Path(settings.storage_root)
    if not base.is_absolute():
        base = BASE_DIR / base
    d = (base / "uploads").resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


async def _run_in_background(task_id: int, code_request: bool) -> None:
    try:
        await TaskService().run_task(task_id, code_request=code_request)
    except Exception as exc:  # noqa: BLE001
        # Persist a failed state so the UI reflects the failure.
        try:
            service = TaskService()
            db = service._db_session()

            db.query(Task).filter(Task.id == task_id).update(
                {Task.status: TaskStatus.FAILED}
            )
            db.commit()
            db.close()
        except Exception:  # noqa: BLE001
            pass
        asyncio.create_task(
            get_event_bus().publish(task_id, {"type": "error", "detail": str(exc)})
        )


@router.post("")
async def create_task(
    prompt: str = Form(...),
    code_request: bool = Form(False),
    file: UploadFile | None = File(None),
    current=Depends(auth.get_current_user),
) -> dict:
    service = TaskService()
    input_source: Path | None = None

    if file is not None and file.filename:
        dest = _upload_dir() / Path(file.filename).name
        data = await file.read()
        dest.write_bytes(data)
        input_source = dest

    task = service.submit_task(
        prompt, user_id=current.id, code_request=code_request, input_source=input_source
    )
    asyncio.create_task(_run_in_background(task.id, code_request))
    return {"task_id": task.id, "status": task.status.value}


@router.get("")
def list_tasks(
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    tasks = (
        db.query(Task).filter(Task.user_id == current.id).order_by(Task.id.desc()).all()
    )
    return [
        {
            "id": t.id,
            "prompt": t.prompt,
            "task_type": t.task_type.value if t.task_type else None,
            "status": t.status.value if t.status else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tasks
    ]


@router.get("/{task_id}")
def task_detail(
    task_id: int,
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None or task.user_id != current.id:
        raise HTTPException(status_code=404, detail="Task not found")

    run = task.runs[-1] if task.runs else None
    steps = (
        [
            {
                "id": s.id,
                "label": s.label,
                "detail": s.detail,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
            }
            for s in run.steps
        ]
        if run
        else []
    )
    tools = (
        [
            {
                "tool_name": te.tool_name,
                "status": te.status.value if te.status else None,
                "risk_level": te.risk_level,
                "duration_ms": te.duration_ms,
            }
            for te in run.tool_executions
        ]
        if run
        else []
    )
    artifacts = (
        [
            {
                    "name": a.name,
                    "kind": a.kind,
                    "id": a.id,
                    "verification_status": (
                    a.verification_status.value if a.verification_status else None
                ),
            }
            for a in run.artifacts
        ]
        if run
        else []
    )
    return {
        "id": task.id,
        "prompt": task.prompt,
        "task_type": task.task_type.value if task.task_type else None,
        "status": task.status.value if task.status else None,
        "workspace": task.workspace,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "run": {
            "id": run.id if run else None,
            "status": run.status.value if run and run.status else None,
            "model_calls": run.model_calls if run else 0,
            "selected_models": run.selected_models if run else [],
            "verification_result": run.verification_result if run else None,
        },
        "steps": steps,
        "tools": tools,
        "artifacts": artifacts,
    }


@router.get("/{task_id}/events")
async def task_events(
    task_id: int,
    token: str | None = Query(None),
) -> StreamingResponse:
    if token:
        try:
            auth.decode_token(token)
        except Exception:  # noqa: BLE001
            raise HTTPException(status_code=401, detail="Invalid token")
    bus = get_event_bus()
    return StreamingResponse(
        bus.subscribe_stream(task_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{task_id}/cancel")
def cancel_task(
    task_id: int,
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None or task.user_id != current.id:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status in (TaskStatus.RECEIVED, TaskStatus.EXECUTING):
        task.status = TaskStatus.CANCELLED
        db.commit()
    return {"task_id": task.id, "status": task.status.value}
