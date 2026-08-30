"""Secure per-task file workspace (AGENTS.md §15, §7).

Each task gets an isolated workspace:
    /workspaces/task-{id}/{input,working,output}

The agent can only resolve paths within its own workspace. Path traversal
(`..`, symlink escape) and arbitrary host paths are blocked. Every path is
validated and normalized.
"""

from __future__ import annotations

from pathlib import Path

from config.settings import BASE_DIR, settings


class PathOutsideWorkspaceError(Exception):
    pass


class Workspace:
    """Provides bounded access to a single task's directory tree."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self._ensure()

    @staticmethod
    def create(workspaces_root: Path, task_id: int | str) -> Workspace:
        task_dir = (workspaces_root / f"task-{task_id}").resolve()
        return Workspace(task_dir)

    def _ensure(self) -> None:
        for sub in ("input", "working", "output"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    def dir(self, name: str) -> Path:
        """Return a subdirectory (input/working/output), validated."""
        if name not in ("input", "working", "output"):
            raise ValueError(f"Unknown workspace directory: {name}")
        path = self.root / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def resolve(self, rel_path: str) -> Path:
        """Resolve a user/LLM-supplied path to an absolute path inside the workspace.

        Blocks traversal outside the workspace and symlink escapes.
        """
        if not rel_path or rel_path.strip() in (".", ".."):
            raise PathOutsideWorkspaceError(f"Invalid path: {rel_path!r}")

        candidate = (self.root / rel_path).resolve()

        # Symlink / traversal escape check
        if not self._is_within(candidate):
            raise PathOutsideWorkspaceError(f"Path escapes workspace: {rel_path!r}")
        return candidate

    def _is_within(self, candidate: Path) -> bool:
        try:
            candidate.relative_to(self.root)
            return True
        except ValueError:
            return False

    # ── convenience helpers ──────────────────────────────────
    def list(self, subdir: str = "working") -> list[str]:
        base = self.dir(subdir)
        return [p.name for p in base.iterdir() if p.is_file()]

    def write_text(self, rel_path: str, content: str, subdir: str = "working") -> Path:
        target = self.resolve(f"{subdir}/{rel_path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def read_text(self, rel_path: str, subdir: str = "working") -> str:
        target = self.resolve(f"{subdir}/{rel_path}")
        if not target.is_file():
            raise FileNotFoundError(str(target))
        return target.read_text(encoding="utf-8")

    def exists(self, rel_path: str, subdir: str = "working") -> bool:
        try:
            target = self.resolve(f"{subdir}/{rel_path}")
        except PathOutsideWorkspaceError:
            return False
        return target.exists()


def get_workspaces_root() -> Path:
    root = Path(settings.storage_root)
    if not root.is_absolute():
        root = BASE_DIR / root
    return root.resolve()


def create_workspace(task_id: int | str) -> Workspace:
    return Workspace.create(get_workspaces_root(), task_id)
