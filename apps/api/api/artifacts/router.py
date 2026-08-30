"""Artifact endpoints: download generated files (AGENTS.md §29: artifacts)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from db.models import Artifact
from db.session import get_db
from security import auth

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


@router.get("/{artifact_id}")
def download_artifact(
    artifact_id: int,
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    art = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if art is None:
        raise HTTPException(status_code=404, detail="Artifact not found")

    path = Path(art.stored_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact file missing on disk")

    media = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "pdf": "application/pdf",
        "txt": "text/plain",
    }.get(art.kind or "", "application/octet-stream")

    return FileResponse(path, media_type=media, filename=art.name)
