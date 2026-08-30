"""Tests for artifact generation and verification."""
from __future__ import annotations

from agent.verifier import Verifier
from artifacts.docx import generate_docx, make_approval_note
from docx import Document


def test_generate_docx_creates_valid_file(tmp_path):
    target = tmp_path / "note.docx"
    generate_docx(
        target,
        title="Approval Note",
        sections=[
            {"heading": "Findings", "body": ["Bearing vibration above limit."]},
            {"heading": "Action", "body": "Perform corrective maintenance."},
        ],
    )
    assert target.exists()

    verifier = Verifier()
    result = verifier.verify_docx_file(
        target,
        required_paragraphs=["Approval Note", "Bearing vibration", "corrective maintenance"],
        required_fields=["Findings", "Action"],
    )
    assert result.passed is True


def test_verifier_fails_when_file_missing(tmp_path):
    verifier = Verifier()
    result = verifier.verify_docx_file(tmp_path / "missing.docx", required_paragraphs=["x"])
    assert result.passed is False
    assert any(not c["ok"] for c in result.checks)


def test_make_approval_note(tmp_path):
    target = tmp_path / "approval.docx"
    make_approval_note(
        target,
        machine_id="MC-1042",
        date="2026-08-20",
        findings=[
            {"item": "Bearing vibration", "status": "FAIL", "remark": "High"},
            {"item": "Oil level", "status": "PASS", "remark": "OK"},
        ],
        sop_references=["Maintenance SOP §4.2"],
        recommendation="Schedule corrective maintenance and re-inspect.",
    )
    verifier = Verifier()
    result = verifier.verify_docx_file(target, required_paragraphs=["Machine ID: MC-1042"])
    assert result.passed is True


def test_make_approval_note_inconclusive_never_approves(tmp_path):
    target = tmp_path / "inconclusive.docx"
    make_approval_note(
        target,
        machine_id="",
        date="2026-08-20",
        findings=[],
        sop_references=["No maintenance SOP retrieved from the knowledge base."],
        recommendation="Manual review required: no inspection items were identified.",
        inconclusive=True,
    )
    doc = Document(str(target))
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "REVIEW REQUIRED" in text
    assert "APPROVED" not in text
    assert "MC-UNKNOWN" not in text
    assert "Not identified in the document" in text
