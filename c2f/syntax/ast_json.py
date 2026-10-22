"""AST → JSON serialisation (CONTRACTS.md section 5). Owner: Kushan.

``ast_to_dict(node)`` produces a JSON-ready dict where every object has
``"type"``, ``"line"``, ``"col"`` plus the node-specific fields.  Operators
are source strings.  Absent optional children are ``null``.  Lists are ``[]``.

The semantic-pass attribute ``expr_type`` is deliberately *not* included
in the JSON output (section 5 contract).
"""
from __future__ import annotations

from typing import Any

from .ast_nodes import (
    ArrayAccess,
    Assign,
    BinaryOp,
    Block,
    Break,
    Call,
    Case,
    Continue,
    DoWhile,
    ExprStmt,
    For,
    Function,
    Identifier,
    If,
    Literal,
    Node,
    Param,
    Program,
    Return,
    Switch,
    UnaryOp,
    VarDecl,
    While,
)


def ast_to_dict(node: Node | None) -> Any:
    """Convert an AST *node* (or ``None``) to a JSON-serialisable value.

    Every object has ``"type"``, ``"line"``, ``"col"`` plus the fields
    defined in CONTRACTS.md section 5.
    """
    if node is None:
        return None

    base: dict[str, Any] = {
        "type": type(node).__name__,
        "line": node.line,
        "col":  node.col,
    }

    # ── top-level ─────────────────────────────────────────────────────
    if isinstance(node, Program):
        base["functions"] = [ast_to_dict(f) for f in node.functions]

    elif isinstance(node, Function):
        base["name"] = node.name
        base["return_type"] = node.return_type
        base["params"] = [_param_to_dict(p) for p in node.params]
        base["body"] = ast_to_dict(node.body)

    # ── statements ────────────────────────────────────────────────────
    elif isinstance(node, Block):
        base["statements"] = [ast_to_dict(s) for s in node.statements]

    elif isinstance(node, VarDecl):
        base["var_type"] = node.var_type
        base["name"] = node.name
        base["array_size"] = node.array_size
        base["init"] = ast_to_dict(node.init)

    elif isinstance(node, ExprStmt):
        base["expr"] = ast_to_dict(node.expr)

    elif isinstance(node, If):
        base["cond"] = ast_to_dict(node.cond)
        base["then"] = ast_to_dict(node.then)
        base["else"] = ast_to_dict(node.else_)

    elif isinstance(node, While):
        base["cond"] = ast_to_dict(node.cond)
        base["body"] = ast_to_dict(node.body)

    elif isinstance(node, DoWhile):
        base["body"] = ast_to_dict(node.body)
        base["cond"] = ast_to_dict(node.cond)

    elif isinstance(node, For):
        base["init"] = ast_to_dict(node.init)
        base["cond"] = ast_to_dict(node.cond)
        base["update"] = ast_to_dict(node.update)
        base["body"] = ast_to_dict(node.body)

    elif isinstance(node, Switch):
        base["expr"] = ast_to_dict(node.expr)
        base["cases"] = [ast_to_dict(c) for c in node.cases]

    elif isinstance(node, Case):
        base["value"] = ast_to_dict(node.value)
        base["body"] = [ast_to_dict(s) for s in node.body]

    elif isinstance(node, Return):
        base["value"] = ast_to_dict(node.value)

    elif isinstance(node, (Break, Continue)):
        pass  # no extra fields

    # ── expressions ───────────────────────────────────────────────────
    elif isinstance(node, Assign):
        base["target"] = ast_to_dict(node.target)
        base["op"] = node.op
        base["value"] = ast_to_dict(node.value)

    elif isinstance(node, BinaryOp):
        base["op"] = node.op
        base["left"] = ast_to_dict(node.left)
        base["right"] = ast_to_dict(node.right)

    elif isinstance(node, UnaryOp):
        base["op"] = node.op
        base["operand"] = ast_to_dict(node.operand)
        base["postfix"] = node.postfix

    elif isinstance(node, Literal):
        base["value"] = node.value
        base["literal_type"] = node.literal_type

    elif isinstance(node, Identifier):
        base["name"] = node.name

    elif isinstance(node, ArrayAccess):
        base["name"] = node.name
        base["index"] = ast_to_dict(node.index)

    elif isinstance(node, Call):
        base["name"] = node.name
        base["args"] = [ast_to_dict(a) for a in node.args]

    return base


def _param_to_dict(p: Param) -> dict[str, str]:
    """Convert a Param to ``{"type": ..., "name": ...}``."""
    return {"type": p.type, "name": p.name}
