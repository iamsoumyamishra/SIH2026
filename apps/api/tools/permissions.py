"""Permission and risk-level policy helpers (AGENTS.md §14, §5.3)."""

from __future__ import annotations

RISK_LEVELS = ("low", "medium", "high")

# Default risk classification for known tools/permissions. Tools added in later
# phases (code execution, artifacts) extend this map.
TOOL_RISK: dict[str, str] = {
    "read_file": "low",
    "list_files": "low",
    "search_files": "low",
    "write_file": "medium",
    "calculator": "low",
}

PERMISSION_RISK: dict[str, str] = {
    "file.read": "low",
    "file.write": "medium",
    "calculator.use": "low",
    "code.execute": "high",
    "code.run_tests": "high",
    "document.read": "low",
    "knowledge.search": "low",
    "artifact.create": "medium",
}


def is_valid_risk(risk: str) -> bool:
    return risk in RISK_LEVELS


def risk_for_tool(name: str) -> str:
    return TOOL_RISK.get(name, "medium")


def risk_for_permission(permission: str) -> str:
    return PERMISSION_RISK.get(permission, "medium")
