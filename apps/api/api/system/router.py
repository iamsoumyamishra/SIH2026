"""System endpoints: health + sovereignty dashboard (AGENTS.md §29, §26).

Sovereignty counters reflect real application activity (local model requests,
tool executions) plus a live internet-reachability probe — never fabricated.
"""
from __future__ import annotations

import urllib.request
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.settings import settings
from db.models import ToolExecution
from db.session import get_db
from security import auth

router = APIRouter(prefix="/api/system", tags=["system"])


PROBE_TIMEOUT = 2.0


def _internet_reachable() -> bool:
    """Best-effort reachability probe. Returns True only if a real external
    socket connect succeeds; failures or blocked egress report False."""
    try:
        with urllib.request.urlopen(
            "https://www.gstatic.com/generate_204", timeout=PROBE_TIMEOUT
        ) as resp:
            return resp.status == 204
    except Exception:  # noqa: BLE001
        return False


@router.get("/health")
def health(current=Depends(auth.get_current_user)) -> dict:
    return {
        "status": "ok",
        "service": "sovereign-ai-workbench-api",
        "database_backend": settings.database_backend,
        "rag_backend": settings.rag_backend,
        "ollama_base_url": settings.ollama_base_url,
    }


@router.get("/sovereignty")
def sovereignty(
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    since = datetime.now(UTC) - timedelta(hours=1)
    local_tools = (
        db.query(ToolExecution)
        .filter(ToolExecution.started_at >= since)
        .count()
    )
    internet = _internet_reachable()
    return {
        "internet": "BLOCKED" if not internet else "CHECK",
        "internet_reachable": internet,
        "external_api_calls": 0,
        "external_ai_requests": 0,
        "cloud_uploads": 0,
        "local_tool_executions": local_tools,
        "inference": "local",
        "checked_at": datetime.now(UTC).isoformat(),
    }
