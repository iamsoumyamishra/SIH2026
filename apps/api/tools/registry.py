"""Central tool registry + permission-aware execution.

The agent can only call tools registered here, and each call is checked against
a permission policy before dispatch (AGENTS.md §14, §13).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tools.base import Tool, ToolBase


class PermissionDeniedError(Exception):
    pass


class ToolNotFoundError(Exception):
    pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        # Available permissions granted to the current agent run.
        self._permissions: set[str] = set()
        self._execution_hooks: list[Callable[[str, str, float], None]] = []

    def register(self, tool: Tool | ToolBase) -> Tool:
        if isinstance(tool, ToolBase):
            instance = tool

            async def handler(context, **kw):
                return await instance.run(context, **kw)

            t = tool.to_tool()
            t.handler = handler
        else:
            t = tool
        self._tools[t.name] = t
        return t

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"Unknown tool: {name}")
        return tool

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def grant_permissions(self, *permissions: str) -> None:
        self._permissions.update(permissions)

    def revoke_permissions(self, *permissions: str) -> None:
        self._permissions.difference_update(permissions)

    def has_permission(self, permission: str) -> bool:
        return permission in self._permissions

    def on_execution(self, hook: Callable[[str, str, float], None]) -> None:
        self._execution_hooks.append(hook)

    async def execute(self, name: str, context, **kwargs) -> dict[str, Any]:
        tool = self.get(name)
        if not self.has_permission(tool.permission):
            raise PermissionDeniedError(
                f"Tool '{name}' requires permission '{tool.permission}' not granted."
            )
        if tool.handler is None:
            raise ToolNotFoundError(f"Tool '{name}' has no handler.")

        import time

        start = time.perf_counter()
        try:
            result = await tool.handler(context=context, **kwargs)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            for hook in self._execution_hooks:
                try:
                    hook(name, tool.risk_level, duration_ms)
                except Exception:
                    pass
        return {"tool": name, "result": result}


_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Return the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def reset_registry() -> None:
    global _registry
    _registry = None
