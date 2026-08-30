"""DOCX artifact generation (AGENTS.md §22 — DOCX is the priority).

Creates real, valid .docx files using python-docx. The agent never returns
markdown pretending to be a document.
"""
from __future__ import annotations

from pathlib import Path

from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


def generate_docx(
    path: str | Path,
    title: str,
    sections: list[dict],
) -> Path:
    """Create a .docx file.

    sections: list of {"heading": str, "body": str or [str]} entries.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = DocxDocument()
    # Title
    h = doc.add_heading(title, level=0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for section in sections:
        heading = section.get("heading")
        body = section.get("body", "")
        if heading:
            doc.add_heading(heading, level=1)
        if isinstance(body, str):
            body = [body]
        for para_text in body:
            p = doc.add_paragraph()
            run = p.add_run(para_text)
            run.font.size = Pt(11)

    doc.save(str(path))
    return path


def make_approval_note(
    path: str | Path,
    machine_id: str,
    date: str,
    findings: list[dict],
    sop_references: list[str],
    recommendation: str,
) -> Path:
    """Generate a standard approval note from inspection findings."""
    ok = [f for f in findings if f.get("status", "").upper() == "PASS"]
    failed = [f for f in findings if f.get("status", "").upper() == "FAIL"]

    sections = [
        {
            "heading": "Machine & Report",
            "body": [
                f"Machine ID: {machine_id}",
                f"Date of inspection: {date}",
                f"Items inspected: {len(findings)}  (Passed: {len(ok)}, Failed: {len(failed)})",
            ],
        },
        {
            "heading": "Findings",
            "body": [
                f"- {f.get('item','')}: {f.get('remark','')}" for f in findings
            ],
        },
        {
            "heading": "Required Action",
            "body": recommendation,
        },
        {
            "heading": "SOP References",
            "body": sop_references or ["-"],
        },
        {
            "heading": "Approval Status",
            "body": (
                "APPROVED for return to service after corrective maintenance "
                "and re-inspection, per maintenance SOP."
                if failed
                else "APPROVED for continued service."
            ),
        },
    ]
    return generate_docx(path, title=f"Inspection Approval Note — {machine_id}", sections=sections)
