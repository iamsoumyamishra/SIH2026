"""Tool definitions: the controlled surface the agent may call.

Every tool declares name, description, input/output schema, permissions and
risk level (AGENTS.md §13). Tools must be registered in the ToolRegistry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Tool:
    name: str
    description: str
    # Permission key, e.g. "document.read", "code.execute", "calculator.use"
    permission: str
    risk_level: str  # low | medium | high
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    handler: Callable[..., Any] | None = None

    def to_openai_schema(self) -> dict[str, Any]:
        """Return the tool in OpenAI tool-calling JSON schema format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


class ToolBase(ABC):
    """Base class for tools that define their metadata as class attributes."""

    name: str = ""
    description: str = ""
    permission: str = ""
    risk_level: str = "low"
    input_schema: dict[str, Any] = {"type": "object", "properties": {}}

    @abstractmethod
    async def run(self, context, **kwargs) -> Any:
        """Execute the tool. `context` carries the agent workspace/deps."""

    def to_tool(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            permission=self.permission,
            risk_level=self.risk_level,
            input_schema=self.input_schema,
        )
