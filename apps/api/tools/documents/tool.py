"""Document extraction tool: routes any file through the local pipeline."""

from __future__ import annotations

from typing import Any

from multimodal.pipeline import DocumentPipeline
from tools.base import ToolBase


class _DocMixin:
    @staticmethod
    def _ws(context: Any):
        ws = getattr(context, "workspace_obj", None)
        if ws is None:
            raise RuntimeError("Workspace not bound to agent context.")
        return ws


class ExtractDocumentTool(_DocMixin, ToolBase):
    name = "extract_document"
    description = (
        "Extract text (and tables) from a workspace file. Handles PDF, image, TXT, DOCX, XLSX."
    )
    permission = "document.read"
    risk_level = "low"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path within workspace, e.g. input/report.pdf",
            },
        },
        "required": ["path"],
    }

    def __init__(self, pipeline: DocumentPipeline | None = None) -> None:
        self.pipeline = pipeline or DocumentPipeline()

    async def run(self, context, **kwargs) -> dict[str, Any]:
        ws = self._ws(context)
        rel = kwargs.get("path", "")
        target = ws.resolve(rel)  # security: bounded path
        if not target.is_file():
            return {"ok": False, "error": f"File not found: {rel}"}
        doc = self.pipeline.ingest(target)
        return {
            "ok": True,
            "filename": doc.filename,
            "content_type": doc.content_type,
            "text": doc.text,
            "page_count": doc.metadata.get("page_count"),
            "tables_count": len(doc.tables),
            "warnings": doc.warnings,
        }
