"""Docker sandbox client.

Runs code inside a throwaway container with no network, an isolated filesystem,
resource limits, and a hard timeout. The host filesystem, secrets, and
environment variables of the host are never exposed.

If the Docker daemon is unavailable, an explicit DockerUnavailableError is
raised — never a silent fallback to running code on the host.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sandbox.policies import SandboxPolicy


class DockerUnavailableError(Exception):
    pass


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int | None
    duration_ms: float
    timed_out: bool = False


class DockerRunner:
    def __init__(self, policy: SandboxPolicy | None = None) -> None:
        self.policy = policy or SandboxPolicy()

    def _client(self):
        try:
            import docker  # type: ignore
        except ImportError as exc:
            raise DockerUnavailableError(
                "Docker Python SDK not installed."
            ) from exc
        try:
            return docker.from_env()
        except Exception as exc:  # noqa: BLE001
            raise DockerUnavailableError(
                "Docker daemon is not available. Start Docker Desktop and "
                "retry; code is never executed directly on the host."
            ) from exc

    def is_available(self) -> bool:
        try:
            self._client()
            return True
        except DockerUnavailableError:
            return False

    def run_python(
        self,
        code: str,
        cwd_files: dict[str, str] | None = None,
        workdir: str | None = None,
    ) -> SandboxResult:
        import docker.errors  # type: ignore

        client = self._client()
        opts = self.policy.to_docker()
        docker_kwargs: dict[str, Any] = {
            "image": self.policy.image,
            "command": ["python", "-c", code],
            "remove": True,
            "detach": True,
            "network_mode": opts["network_mode"],
            "cpus": opts["cpus"],
            "mem_limit": opts["mem_limit"],
            "pids_limit": opts["pids_limit"],
        }

        # Mount provided files into a working directory (isolated, not host fs).
        volumes: dict[str, dict[str, str]] = {}
        if cwd_files:
            tmp = Path(__file__).resolve().parent / "_mounts"
            for name, content in cwd_files.items():
                target = (tmp / name).resolve()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                volumes[str(target)] = {"bind": f"/work/{name}", "mode": "ro"}
            docker_kwargs["volumes"] = volumes
            docker_kwargs["working_dir"] = "/work"
        elif workdir:
            docker_kwargs["working_dir"] = workdir

        start = time.perf_counter()
        container = None
        timed_out = False
        try:
            container = client.containers.run(**docker_kwargs)
            try:
                result = container.wait(timeout=self.policy.timeout_seconds)
                exit_code = int(result.get("StatusCode", -1))
                logs = container.logs(stdout=True, stderr=True).decode(
                    "utf-8", errors="replace"
                )
            except docker.errors.NotFound:
                exit_code = -1
                logs = ""
        except docker.errors.APIError as exc:
            raise DockerUnavailableError(str(exc))
        except Exception as exc:  # noqa: BLE001
            if "timed out" in str(exc).lower() or "Http response was aborted" in str(exc):
                timed_out = True
                exit_code = -1
                logs = ""
            else:
                raise
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:  # noqa: BLE001
                    pass
            # always attempt to reap the image-triggered container leftovers
            try:
                client.containers.prune()
            except Exception:  # noqa: BLE001
                pass

        duration_ms = (time.perf_counter() - start) * 1000
        # docker attaches stderr+stdout together; we expose combined logs.
        return SandboxResult(
            stdout=logs.strip(),
            stderr="",
            exit_code=exit_code,
            duration_ms=duration_ms,
            timed_out=timed_out,
        )
