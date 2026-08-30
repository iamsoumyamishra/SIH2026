"""Sandbox manager: the only way the agent executes untrusted code.

Provides a high-level interface for the code tools. All execution goes through
the Docker runner; if Docker is unavailable it returns a structured failure so
the agent observes it and can replan — never runs on the host.
"""
from __future__ import annotations

from typing import Any

from sandbox.docker import DockerRunner, DockerUnavailableError, SandboxResult


class SandboxManager:
    def __init__(self, runner: DockerRunner | None = None) -> None:
        self.runner = runner or DockerRunner()

    def is_available(self) -> bool:
        return self.runner.is_available()

    def execute_python(self, code: str) -> dict[str, Any]:
        """Execute Python code in the sandbox and return a structured result."""
        r: SandboxResult | None = None
        error: str | None = None
        try:
            r = self.runner.run_python(code)
        except DockerUnavailableError as exc:
            error = str(exc)
        except Exception as exc:  # noqa: BLE001
            error = f"Sandbox execution error: {exc}"

        if error is not None:
            return {
                "ok": False,
                "error": error,
                "stdout": "",
                "stderr": "",
                "exit_code": None,
                "timed_out": False,
            }
        return {
            "ok": r.exit_code == 0,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "exit_code": r.exit_code,
            "timed_out": r.timed_out,
            "duration_ms": r.duration_ms,
        }

    def run_code_with_files(self, code: str, files: dict[str, str]) -> dict[str, Any]:
        """Execute code with helper files mounted read-only into the container."""
        try:
            r = self.runner.run_python(code, cwd_files=files)
        except DockerUnavailableError as exc:
            return {"ok": False, "error": str(exc), "stdout": "", "exit_code": None}
        return {
            "ok": r.exit_code == 0,
            "stdout": r.stdout,
            "exit_code": r.exit_code,
            "timed_out": r.timed_out,
        }
