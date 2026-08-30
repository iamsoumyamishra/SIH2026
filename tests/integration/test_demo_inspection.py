"""Integration test: primary inspection report → approval note demo.

Verifies the full agent stack end-to-end using a deterministic (non-LLM) path:
upload inspection PDF → OCR/text extract → parse findings → RAG over SOP →
analyze → generate + verify approval_note.docx.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.session import Base
from rag.ingestion import IngestionService
from services.task_service import TaskService

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_PDF = REPO_ROOT / "sample_documents" / "inspection_report.pdf"
SAMPLE_SOP = REPO_ROOT / "datasets" / "maintenance_sop.txt"


@pytest.fixture
def session(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    db = Session()
    yield db
    db.close()
    engine.dispose()


def test_inspection_to_approval_note(session):
    if not SAMPLE_PDF.exists():
        pytest.skip("sample inspection PDF not present")

    # Preload the maintenance SOP into the shared local vector store so that
    # the RAG step has real content to retrieve (best-effort: if Ollama or the
    # embedding service is unavailable, the deterministic demo still succeeds).
    if SAMPLE_SOP.exists():
        try:
            IngestionService().ingest_text(
                SAMPLE_SOP.read_text(encoding="utf-8"),
                document_id="maintenance_sop",
                document_name="Maintenance SOP",
                section="General",
                version="1.0",
            )
        except Exception:  # noqa: BLE001
            pass

    svc = TaskService(db=session)
    out = asyncio.run(
        svc.create_and_run(
            prompt=(
                "Analyze this scanned inspection report and compare findings "
                "against the maintenance SOP, then generate an approval note."
            ),
            user_id=1,
            input_source=SAMPLE_PDF,
        )
    )

    assert out.status == "completed"
    s = out.summary
    assert s["task_type"] == "multimodal"
    names = [a["name"] for a in s["artifacts"]]
    assert "approval_note.docx" in names
    assert s["verification"].get("passed") is True
