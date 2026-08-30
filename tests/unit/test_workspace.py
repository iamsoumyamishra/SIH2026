"""Tests for the secure per-task workspace and path validation."""
from __future__ import annotations

import pytest

from tools.filesystem.workspace import (
    PathOutsideWorkspaceError,
    Workspace,
)


def test_creates_subdirectories(tmp_path):
    ws = Workspace(tmp_path / "task-1")
    for sub in ("input", "working", "output"):
        assert (ws.root / sub).is_dir()


def test_write_and_read(tmp_path):
    ws = Workspace(tmp_path / "t")
    p = ws.write_text("a/b.txt", "hello world", subdir="working")
    assert p.is_file()
    assert ws.read_text("a/b.txt") == "hello world"


def test_blocks_parent_traversal(tmp_path):
    ws = Workspace(tmp_path / "t")
    with pytest.raises(PathOutsideWorkspaceError):
        ws.resolve("../secret.txt")


def test_blocks_absolute_escape(tmp_path):
    ws = Workspace(tmp_path / "t")
    with pytest.raises(PathOutsideWorkspaceError):
        ws.resolve(str(tmp_path / "outside.txt"))


def test_blocks_embedded_traversal(tmp_path):
    ws = Workspace(tmp_path / "t")
    with pytest.raises(PathOutsideWorkspaceError):
        ws.resolve("working/../../evilsl")


def test_resolve_within_allowed(tmp_path):
    ws = Workspace(tmp_path / "t")
    p = ws.resolve("working/x.txt")
    assert p == (ws.root / "working" / "x.txt").resolve()


def test_list_only_files(tmp_path):
    ws = Workspace(tmp_path / "t")
    ws.write_text("one.txt", "1", subdir="working")
    ws.write_text("two.txt", "2", subdir="working")
    (ws.root / "working" / "sub").mkdir(exist_ok=True)
    names = ws.list("working")
    assert set(names) == {"one.txt", "two.txt"}
