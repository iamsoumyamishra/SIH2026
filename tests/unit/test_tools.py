"""Tests for the tool registry, permissions, and built-in tools."""
from __future__ import annotations

import asyncio

import pytest

from tools.calculator.tool import CalculatorTool, UnsafeExpressionError, safe_eval
from tools.filesystem.workspace import Workspace
from tools.registry import PermissionDeniedError, ToolRegistry
from tools.setup import build_registry


class _Ctx:
    def __init__(self, ws):
        self.workspace_obj = ws


# ── calculator ───────────────────────────────────────────────
def test_safe_eval_basic():
    assert safe_eval("2 + 3 * 4") == 14.0


def test_safe_eval_unsafe_rejected():
    with pytest.raises(UnsafeExpressionError):
        safe_eval("__import__('os').system('id')")
    with pytest.raises(UnsafeExpressionError):
        safe_eval("1; 2")


def test_calculator_tool(tmp_path):
    ws = Workspace(tmp_path / "t")
    reg = build_registry()
    ctx = _Ctx(ws)

    async def run():
        return await reg.execute("calculator", ctx, expression="10 / 4")

    res = asyncio.run(run())
    assert res["result"]["ok"] is True
    assert res["result"]["result"] == 2.5


# ── filesystem tools ─────────────────────────────────────────
def test_write_read_file_via_registry(tmp_path):
    reg = build_registry()
    ctx = _Ctx(Workspace(tmp_path / "t"))

    async def go():
        w = await reg.execute("write_file", ctx, path="a.txt", content="hi", subdir="working")
        r = await reg.execute("read_file", ctx, path="a.txt")
        return w, r

    w, r = asyncio.run(go())
    assert w["result"]["ok"] is True
    assert r["result"]["content"] == "hi"


def test_list_and_search(tmp_path):
    reg = build_registry()
    ws = Workspace(tmp_path / "t")
    ws.write_text("note.pdf", "x", subdir="input")
    ctx = _Ctx(ws)

    async def go():
        listing = await reg.execute("list_files", ctx, subdir="input")
        search = await reg.execute("search_files", ctx, pattern="*.pdf", subdir="input")
        return listing, search

    listing, search = asyncio.run(go())
    assert listing["result"]["files"] == ["note.pdf"]
    assert search["result"]["matches"] == ["note.pdf"]


def test_permission_denied_without_grant(tmp_path):
    reg = ToolRegistry()
    reg.register(CalculatorTool())  # no permission granted
    ctx = _Ctx(Workspace(tmp_path / "t"))

    async def run():
        return await reg.execute("calculator", ctx, expression="1+1")

    with pytest.raises(PermissionDeniedError):
        asyncio.run(run())


def test_unknown_tool_raises(tmp_path):
    reg = build_registry()
    ctx = _Ctx(Workspace(tmp_path / "t"))

    async def run():
        return await reg.execute("does_not_exist", ctx)

    with pytest.raises(Exception):
        asyncio.run(run())
