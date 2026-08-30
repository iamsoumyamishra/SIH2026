"""Filesystem tools. All operate strictly within the task workspace container.

The agent cannot reference arbitrary host paths — only relative paths inside the
task's workspace (input/working/output directories).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.base import ToolBase


class _FilesystemContextMixin:
    """Extracts the Workspace from the agent execution context."""

    @staticmethod
    def _ws(context: Any):
        ws = getattr(context, "workspace_obj", None)
        if ws is None:
            raise RuntimeError("Workspace not bound to agent context.")
        return ws


class ReadFileTool(_FilesystemContextMixin, ToolBase):
    name = "read_file"
    description = "Read a text file from the task workspace (relative path)."
    permission = "file.read"
    risk_level = "low"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path within the workspace (e.g. input/report.txt)",
            },
        },
        "required": ["path"],
    }

    async def run(self, context, **kwargs) -> dict[str, Any]:
        ws = self._ws(context)
        rel = kwargs.get("path", "")
        content = ws.read_text(rel)
        return {"ok": True, "content": content, "path": rel}


class WriteFileTool(_FilesystemContextMixin, ToolBase):
    name = "write_file"
    description = "Write a text file into the task workspace (relative path)."
    permission = "file.write"
    risk_level = "medium"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "subdir": {"type": "string", "enum": ["input", "working", "output"]},
        },
        "required": ["path", "content"],
    }

    async def run(self, context, **kwargs) -> dict[str, Any]:
        ws = self._ws(context)
        rel = kwargs.get("path", "")
        content = kwargs.get("content", "")
        subdir = kwargs.get("subdir", "working")
        target = ws.write_text(rel, content, subdir=subdir)
        return {"ok": True, "path": str(target)}


class ListFilesTool(_FilesystemContextMixin, ToolBase):
    name = "list_files"
    description = "List files in a workspace directory (input/working/output)."
    permission = "file.read"
    risk_level = "low"
    input_schema = {
        "type": "object",
        "properties": {
            "subdir": {
                "type": "string",
                "enum": ["input", "working", "output"],
                "default": "working",
            },
        },
    }

    async def run(self, context, **kwargs) -> dict[str, Any]:
        ws = self._ws(context)
        subdir = kwargs.get("subdir", "working")
        files = ws.list(subdir)
        return {"ok": True, "files": files, "subdir": subdir}


class SearchFilesTool(_FilesystemContextMixin, ToolBase):
    name = "search_files"
    description = "Search file names in the workspace matching a glob pattern."
    permission = "file.read"
    risk_level = "low"
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "glob like *.pdf"},
            "subdir": {"type": "string", "default": "input"},
        },
    }

    async def run(self, context, **kwargs) -> dict[str, Any]:
        ws = self._ws(context)
        pattern = kwargs.get("pattern", "*")
        subdir = kwargs.get("subdir", "input")
        base: Path = ws.dir(subdir)
        matches = [str(p.relative_to(base)) for p in base.glob(pattern) if p.is_file()]
        return {"ok": True, "matches": matches, "subdir": subdir}
