"""RAG tools: search the local knowledge base and ingest documents."""

from __future__ import annotations

from typing import Any

from rag.ingestion import IngestionService
from rag.retrieval import RetrievalService
from tools.base import ToolBase


class _RagMixin:
    @staticmethod
    def _ws(context: Any):
        ws = getattr(context, "workspace_obj", None)
        if ws is None:
            raise RuntimeError("Workspace not bound to agent context.")
        return ws


class SearchKnowledgeTool(_RagMixin, ToolBase):
    name = "search_knowledge"
    description = "Search the local knowledge base by semantic query."
    permission = "knowledge.search"
    risk_level = "low"
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The question/keywords to search for"},
            "limit": {"type": "integer"},
        },
        "required": ["query"],
    }

    def __init__(self, retrieval: RetrievalService | None = None) -> None:
        self.retrieval = retrieval or RetrievalService()

    async def run(self, context, **kwargs) -> dict[str, Any]:
        query = kwargs.get("query", "")
        limit = int(kwargs.get("limit", 5))
        if not query.strip():
            return {"ok": False, "error": "Empty query."}
        try:
            result = self.retrieval.search(query, limit=limit)
            return {"ok": True, **result}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"Knowledge search failed: {exc}"}


class IngestKnowledgeTool(_RagMixin, ToolBase):
    name = "ingest_knowledge"
    description = "Ingest a workspace text file into the local knowledge base (RAG)."
    permission = "knowledge.ingest"
    risk_level = "medium"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "document_id": {"type": "string"},
            "document_name": {"type": "string"},
        },
    }

    def __init__(self, ingestion: IngestionService | None = None) -> None:
        self.ingestion = ingestion or IngestionService()

    async def run(self, context, **kwargs) -> dict[str, Any]:
        ws = self._ws(context)
        rel = kwargs.get("path", "")
        target = ws.resolve(rel)
        if not target.is_file():
            return {"ok": False, "error": f"File not found: {rel}"}
        text = target.read_text(encoding="utf-8", errors="replace")
        doc_id = kwargs.get("document_id") or target.stem
        doc_name = kwargs.get("document_name") or target.name
        try:
            result = self.ingestion.ingest_text(text, document_id=doc_id, document_name=doc_name)
            return {"ok": True, **result}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"Ingestion failed: {exc}"}
