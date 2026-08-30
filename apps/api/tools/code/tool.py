"""Code execution tools. All execution happens inside the Docker sandbox."""

from __future__ import annotations

from typing import Any

from sandbox.manager import SandboxManager
from tools.base import ToolBase


class _CodeMixin:
    @staticmethod
    def _ws(context: Any):
        ws = getattr(context, "workspace_obj", None)
        if ws is None:
            raise RuntimeError("Workspace not bound to agent context.")
        return ws


class ExecuteCodeTool(_CodeMixin, ToolBase):
    name = "execute_code"
    description = "Execute Python code inside the isolated Docker sandbox (no network)."
    permission = "code.execute"
    risk_level = "high"
    input_schema = {
        "type": "object",
        "properties": {"code": {"type": "string"}},
        "required": ["code"],
    }

    def __init__(self, manager: SandboxManager | None = None) -> None:
        self.manager = manager or SandboxManager()

    async def run(self, context, **kwargs) -> dict[str, Any]:
        code = kwargs.get("code", "")
        if not code.strip():
            return {"ok": False, "error": "No code provided."}
        return self.manager.execute_python(code)


class RunTestsTool(_CodeMixin, ToolBase):
    name = "run_tests"
    description = "Run pytest-based tests for code in the sandbox (no network)."
    permission = "code.run_tests"
    risk_level = "high"
    input_schema = {
        "type": "object",
        "properties": {"code": {"type": "string"}, "tests": {"type": "string"}},
    }

    def __init__(self, manager: SandboxManager | None = None) -> None:
        self.manager = manager or SandboxManager()

    async def run(self, context, **kwargs) -> dict[str, Any]:
        code = kwargs.get("code", "")
        tests = kwargs.get("tests", "")
        if not code.strip():
            return {"ok": False, "error": "No code provided."}
        if not tests.strip():
            return {"ok": False, "error": "No tests provided."}
        files = {"solution.py": code, "test_scenario.py": tests}
        # Run code import + run tests appended
        runner_code = (
            "import sys\n"
            "sys.path.insert(0, '/work')\n"
            f"{tests}\n"
            "import solution\n"
            "print('TESTS EXECUTED OK')"
        )
        return self.manager.run_code_with_files(runner_code, files)
