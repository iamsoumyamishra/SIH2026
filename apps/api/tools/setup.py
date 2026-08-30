"""Standard toolset factory for an agent run.

Builds a ToolRegistry pre-populated with the default tools and grants the
permission set appropriate for a task. Tools are added incrementally as new
capabilities (documents, vision, rag, code, artifacts) are implemented.
"""
from __future__ import annotations

from tools.artifacts.tool import (
    CreateDocxTool,
    CreatePdfTool,
    CreatePptxTool,
    CreateXlsxTool,
)
from tools.calculator.tool import CalculatorTool
from tools.code.tool import ExecuteCodeTool, RunTestsTool
from tools.documents.tool import ExtractDocumentTool
from tools.filesystem.tools import ListFilesTool, ReadFileTool, SearchFilesTool, WriteFileTool
from tools.rag.tool import IngestKnowledgeTool, SearchKnowledgeTool
from tools.registry import ToolRegistry

# Standard set of permissions a normal (non-privileged) run may use.
DEFAULT_PERMISSIONS = {
    "file.read",
    "file.write",
    "calculator.use",
    "document.read",
    "knowledge.search",
    "knowledge.ingest",
    "artifact.create",
}

# High-risk permissions granted only when explicitly requested for a task.
CODE_PERMISSIONS = {"code.execute", "code.run_tests"}


def build_registry(
    permissions: set[str] | None = None,
    include_rag: bool = True,
    include_documents: bool = True,
    include_code: bool = False,
) -> ToolRegistry:
    registry = ToolRegistry()
    for tool in (
        ReadFileTool(),
        WriteFileTool(),
        ListFilesTool(),
        SearchFilesTool(),
        CalculatorTool(),
        CreateDocxTool(),
        CreateXlsxTool(),
        CreatePptxTool(),
        CreatePdfTool(),
    ):
        registry.register(tool)

    if include_documents:
        registry.register(ExtractDocumentTool())
    if include_rag:
        registry.register(SearchKnowledgeTool())
        registry.register(IngestKnowledgeTool())
    if include_code:
        registry.register(ExecuteCodeTool())
        registry.register(RunTestsTool())

    granted = set(permissions) if permissions is not None else set(DEFAULT_PERMISSIONS)
    registry.grant_permissions(*granted)
    return registry
