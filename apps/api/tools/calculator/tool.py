"""Calculator tool.

Evaluates arithmetic expressions without executing arbitrary code. Uses Python's
AST to whitelist safe operators and numeric literals. No shell, no imports.
"""
from __future__ import annotations

import ast
import operator
from typing import Any

from tools.base import ToolBase

_BIN_OPS: dict[type, object] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS: dict[type, object] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class UnsafeExpressionError(Exception):
    pass


def safe_eval(expr: str) -> float:
    """Evaluate a safe arithmetic expression to a number."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpressionError(f"Invalid expression: {exc}") from exc
    return _eval_node(tree.body)


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return float(_BIN_OPS[type(node.op)](left, right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return float(_UNARY_OPS[type(node.op)](_eval_node(node.operand)))
    raise UnsafeExpressionError(f"Expression contains unsupported syntax: {type(node).__name__}")


class CalculatorTool(ToolBase):
    name = "calculator"
    description = "Evaluate a safe arithmetic expression (e.g. '2 + 3 * 4')."
    permission = "calculator.use"
    risk_level = "low"
    input_schema = {
        "type": "object",
        "properties": {
            "expression": {"type": "string"},
        },
        "required": ["expression"],
    }

    async def run(self, context, **kwargs) -> dict[str, Any]:
        expr = kwargs.get("expression", "")
        try:
            value = safe_eval(expr)
            return {"ok": True, "expression": expr, "result": value}
        except UnsafeExpressionError as exc:
            return {"ok": False, "error": str(exc)}
