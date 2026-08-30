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
        # Import the solution first, expose its names so bare-name references
        # work, and stub `pytest` (slim images have no pytest; we run tests via
        # introspection instead). Then run every test_* function AND any
        # unittest.TestCase so asserts genuinely execute. None discovered is a
        # failure, not a pass.
        runner_code = (
            "import sys as _sys\n"
            "import types as _types\n"
            "_pytest = _types.ModuleType('pytest')\n"
            "_pytest.mark = _types.SimpleNamespace()\n"
            "_sys.modules['pytest'] = _pytest\n"
            "import solution\n"
            "for _n in dir(solution):\n"
            "    if not _n.startswith('__'):\n"
            "        globals().setdefault(_n, getattr(solution, _n))\n"
        ) + tests + (
            "\nimport unittest as _u\n"
            "_fns = [globals()[n] for n in list(globals()) "
            "if n.startswith('test_') and callable(globals()[n])]\n"
            "_cases = [v for v in list(globals().values()) "
            "if isinstance(v, type) and issubclass(v, _u.TestCase)]\n"
            "if not _fns and not _cases:\n"
            "    print('ERROR: no runnable tests defined')\n"
            "    raise SystemExit(2)\n"
            "for _t in _fns:\n"
            "    _t()\n"
            "for _c in _cases:\n"
            "    _suite = _u.defaultTestLoader.loadTestsFromTestCase(_c)\n"
            "    _res = _u.TextTestRunner(verbosity=2, stream=_sys.stdout).run(_suite)\n"
            "    if not _res.wasSuccessful():\n"
            "        raise SystemExit(1)\n"
            "print('TESTS EXECUTED OK')\n"
        )
        return self.manager.run_code_with_files(runner_code, files)
