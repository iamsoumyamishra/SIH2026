"""Artifact generation tools.

These create real, verifiable files (DOCX priority, plus XLSX/PPTX/PDF/TXT) in
the task's output directory. See artifacts/ for the concrete generators.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from artifacts.docx import generate_docx
from artifacts.pdf import generate_pdf
from artifacts.pptx import generate_pptx
from artifacts.xlsx import generate_xlsx
from tools.base import ToolBase


class CreateDocxTool(ToolBase):
    name = "create_docx"
    description = "Generate a Word (.docx) document with title and heading/body sections."
    permission = "artifact.create"
    risk_level = "medium"
    input_schema = {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "title": {"type": "string"},
            "sections": {
                "type": "array",
                "items": {"type": "object"},
                "description": "list of {heading, body}",
            },
        },
        "required": ["filename", "title", "sections"],
    }

    @staticmethod
    def _output_dir(context: Any) -> Path:
        ws = getattr(context, "workspace_obj", None)
        if ws is None:
            raise RuntimeError("Workspace not bound to agent context.")
        return ws.dir("output")

    async def run(self, context, **kwargs) -> dict[str, Any]:
        filename = kwargs.get("filename", "artifact.docx")
        title = kwargs.get("title", "Document")
        sections = kwargs.get("sections", []) or []
        # Accept sections as JSON string too (from LLM tool-call payloads).
        if isinstance(sections, str):
            try:
                sections = json.loads(sections)
            except json.JSONDecodeError:
                sections = [{"body": sections}]

        out = self._output_dir(context)
        # Sanitize filename: no traversal.
        safe_name = Path(filename).name
        target = out / safe_name
        generate_docx(target, title=title, sections=sections)
        return {
            "ok": True,
            "artifact": str(target),
            "kind": "docx",
            "name": safe_name,
        }


class CreateXlsxTool(ToolBase):
    name = "create_xlsx"
    description = "Generate an Excel (.xlsx) workbook with headers and rows."
    permission = "artifact.create"
    risk_level = "medium"
    input_schema = {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "sheet_name": {"type": "string", "default": "Sheet1"},
            "headers": {"type": "array", "items": {"type": "string"}},
            "rows": {"type": "array"},
        },
        "required": ["filename", "headers", "rows"],
    }

    @staticmethod
    def _output_dir(context: Any) -> Path:
        ws = getattr(context, "workspace_obj", None)
        if ws is None:
            raise RuntimeError("Workspace not bound to agent context.")
        return ws.dir("output")

    async def run(self, context, **kwargs) -> dict[str, Any]:
        filename = kwargs.get("filename", "data.xlsx")
        out = self._output_dir(context)
        safe_name = Path(filename).name
        generate_xlsx(
            out / safe_name,
            sheet_name=kwargs.get("sheet_name", "Sheet1"),
            headers=kwargs.get("headers", []),
            rows=kwargs.get("rows", []),
        )
        return {"ok": True, "artifact": str(out / safe_name), "kind": "xlsx", "name": safe_name}


class CreatePptxTool(ToolBase):
    name = "create_pptx"
    description = "Generate a PowerPoint (.pptx) presentation."
    permission = "artifact.create"
    risk_level = "medium"
    input_schema = {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "title": {"type": "string"},
            "slides": {"type": "array"},
        },
    }

    @staticmethod
    def _output_dir(context: Any) -> Path:
        ws = getattr(context, "workspace_obj", None)
        if ws is None:
            raise RuntimeError("Workspace not bound to agent context.")
        return ws.dir("output")

    async def run(self, context, **kwargs) -> dict[str, Any]:
        filename = kwargs.get("filename", "deck.pptx")
        out = self._output_dir(context)
        safe_name = Path(filename).name
        generate_pptx(
            out / safe_name,
            title=kwargs.get("title", "Presentation"),
            slides=kwargs.get("slides", []),
        )
        return {"ok": True, "artifact": str(out / safe_name), "kind": "pptx", "name": safe_name}


class CreatePdfTool(ToolBase):
    name = "create_pdf"
    description = "Generate a PDF document with title and sections."
    permission = "artifact.create"
    risk_level = "medium"
    input_schema = {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "title": {"type": "string"},
            "sections": {"type": "array"},
        },
    }

    @staticmethod
    def _output_dir(context: Any) -> Path:
        ws = getattr(context, "workspace_obj", None)
        if ws is None:
            raise RuntimeError("Workspace not bound to agent context.")
        return ws.dir("output")

    async def run(self, context, **kwargs) -> dict[str, Any]:
        filename = kwargs.get("filename", "doc.pdf")
        out = self._output_dir(context)
        safe_name = Path(filename).name
        generate_pdf(
            out / safe_name,
            title=kwargs.get("title", "Document"),
            sections=kwargs.get("sections", []),
        )
        return {"ok": True, "artifact": str(out / safe_name), "kind": "pdf", "name": safe_name}
