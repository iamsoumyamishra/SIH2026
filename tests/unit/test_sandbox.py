"""Tests for the sandbox manager (graceful Docker-unavailable behavior)."""
from __future__ import annotations

from sandbox.docker import DockerUnavailableError
from sandbox.manager import SandboxManager


class _UnavailableRunner:
    def is_available(self) -> bool:
        return False

    def run_python(self, *args, **kwargs):
        raise DockerUnavailableError("Docker daemon is not available.")


def test_manager_returns_structured_failure_when_docker_unavailable():
    manager = SandboxManager(runner=_UnavailableRunner())  # type: ignore[arg-type]
    result = manager.execute_python("print('hi')")
    assert result["ok"] is False
    assert "Docker" in result["error"]
    assert result["exit_code"] is None


def test_manager_is_available_false():
    manager = SandboxManager(runner=_UnavailableRunner())  # type: ignore[arg-type]
    assert manager.is_available() is False
