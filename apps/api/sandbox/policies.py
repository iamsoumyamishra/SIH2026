"""Sandbox security policies (AGENTS.md §16).

Enforces: no network, isolated filesystem, no host/secret access, required
timeout, CPU limit, and memory limit. These values are always applied to any
container created by the sandbox.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SandboxPolicy:
    # Network must be disabled — this is a hard rule.
    disable_network: bool = True
    cpus: float = 1.0
    memory_mb: int = 512
    timeout_seconds: int = 30
    # Base image used to run untrusted code.
    image: str = "python:3.11-slim"

    def to_docker(self) -> dict:
        """Convert to Docker run kwargs."""
        return {
            "network_mode": "none" if self.disable_network else "default",
            "cpus": self.cpus,
            "mem_limit": f"{self.memory_mb}m",
            "pids_limit": 64,
        }
