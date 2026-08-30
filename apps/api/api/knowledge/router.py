"""Knowledge / RAG endpoints (AGENTS.md §29: knowledge).

Everything runs locally: ingest → chunk → embed → local store; search → embed →
retrieve with source metadata for citations.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.models import Document
from db.session import get_db
from rag.ingestion import IngestionService
from rag.retrieval import RetrievalService
from security import auth

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class IngestRequest(BaseModel):
    document_id: str
    document_name: str = ""
    text: str | None = None
    section: str | None = None
    version: str | None = None
    classification: str | None = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    min_score: float = 0.0


@router.post("/ingest")
def ingest(
    request: IngestRequest,
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not request.text:
        raise HTTPException(status_code=400, detail="text is required")

    svc = IngestionService()
    try:
        result = svc.ingest_text(
            request.text,
            document_id=request.document_id,
            document_name=request.document_name,
            section=request.section,
            version=request.version,
            classification=request.classification,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")

    # Metadata-only record (never store full contents in the DB).
    doc = Document(
        filename=request.document_name or request.document_id,
        stored_path="knowledge://" + request.document_id,
        content_type="text",
        text_preview=request.text[:2000],
    )
    db.add(doc)
    db.commit()
    result["document_db_id"] = doc.id
    return result


@router.post("/search")
def search(
    request: SearchRequest,
    current=Depends(auth.get_current_user),
) -> dict:
    svc = RetrievalService()
    try:
        return svc.search(request.query, limit=request.limit, min_score=request.min_score)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}")
