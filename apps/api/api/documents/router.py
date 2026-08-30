"""Document endpoints (AGENTS.md §29: documents).

Uploads are stored on disk; the DB keeps metadata + a safe text preview only
(never full confidential contents).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from config.settings import BASE_DIR, settings
from db.models import Document
from db.session import get_db
from multimodal.pipeline import DocumentPipeline
from security import auth

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _upload_dir() -> Path:
    base = Path(settings.storage_root)
    if not base.is_absolute():
        base = BASE_DIR / base
    d = (base / "uploads").resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Empty filename")

    safe_name = Path(file.filename).name
    dest = _upload_dir() / safe_name
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    dest.write_bytes(data)

    content_type = "unknown"
    text_preview: str | None = None
    page_count = 0
    try:
        util = DocumentPipeline().ingest(dest)
        content_type = util.content_type
        text_preview = (util.text or "")[:2000] or None
        page_count = util.page_count if hasattr(util, "page_count") else 0
    except Exception:  # noqa: BLE001
        pass

    doc = Document(
        filename=safe_name,
        stored_path=str(dest),
        mime_type=file.content_type,
        content_type=content_type,
        text_preview=text_preview,
        page_count=page_count,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "content_type": doc.content_type,
        "page_count": doc.page_count,
    }


@router.get("")
def list_documents(
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    docs = db.query(Document).order_by(Document.id.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "content_type": d.content_type,
            "page_count": d.page_count,
            "text_preview": d.text_preview,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@router.get("/{doc_id}")
def document_detail(
    doc_id: int,
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "filename": doc.filename,
        "content_type": doc.content_type,
        "page_count": doc.page_count,
        "text_preview": doc.text_preview,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }
