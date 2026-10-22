"""Tests for c2f.syntax.ast_nodes (imports the module directly: Kushan's own internals)."""

import dataclasses

import pytest

from c2f.syntax import ast_nodes as A

P = {"line": 1, "col": 1}

ALL_NODES = [
    A.Program, A.Function, A.Block, A.VarDecl, A.ExprStmt, A.If, A.While,
    A.DoWhile, A.For, A.Switch, A.Case, A.Return, A.Break, A.Continue,
    A.Assign, A.BinaryOp, A.UnaryOp, A.Literal, A.Identifier, A.ArrayAccess, A.Call,
]


def fields(cls):
    return [f.name for f in dataclasses.fields(cls)]


def test_all_21_contract_nodes_exist_and_are_nodes():
    assert len(ALL_NODES) == 21
    for cls in ALL_NODES:
        assert dataclasses.is_dataclass(cls)
        assert issubclass(cls, A.Node)
        assert fields(cls)[:2] == ["line", "col"]


@pytest.mark.parametrize(
    "cls, expected",
    [
        (A.Program, ["functions"]),
        (A.Function, ["name", "return_type", "params", "body"]),
        (A.Block, ["statements"]),
        (A.VarDecl, ["var_type", "name", "array_size", "init"]),
        (A.ExprStmt, ["expr"]),
        (A.If, ["cond", "then", "else_"]),
        (A.While, ["cond", "body"]),
        (A.DoWhile, ["body", "cond"]),
        (A.For, ["init", "cond", "update", "body"]),
        (A.Switch, ["expr", "cases"]),
        (A.Case, ["value", "body"]),
        (A.Return, ["value"]),
        (A.Break, []),
        (A.Continue, []),
        (A.Assign, ["target", "op", "value"]),
        (A.BinaryOp, ["op", "left", "right"]),
        (A.UnaryOp, ["op", "operand", "postfix"]),
        (A.Literal, ["value", "literal_type"]),
        (A.Identifier, ["name"]),
        (A.ArrayAccess, ["name", "index"]),
        (A.Call, ["name", "args"]),
    ],
)
def test_fields_match_contract(cls, expected):
    assert fields(cls)[2:] == expected


def test_hierarchy():
    for cls in (A.Assign, A.BinaryOp, A.UnaryOp, A.Literal, A.Identifier,
                A.ArrayAccess, A.Call):
        assert issubclass(cls, A.Expr)
    for cls in (A.Block, A.VarDecl, A.ExprStmt, A.If, A.While, A.DoWhile, A.For,
                A.Switch, A.Return, A.Break, A.Continue):
        assert issubclass(cls, A.Stmt)


def test_build_small_tree():
    cond = A.BinaryOp(op=">", left=A.Identifier(name="x", **P),
                      right=A.Literal(value="5", literal_type="int", **P), **P)
    node = A.If(cond=cond, then=A.Block(statements=[], **P), else_=None, **P)
    assert node.cond.op == ">"
    assert node.else_ is None
    assert node.line == 1 and node.col == 1


def test_expr_type_is_attribute_not_field():
    ident = A.Identifier(name="x", **P)
    assert ident.expr_type is None
    assert "expr_type" not in fields(A.Identifier)
    ident.expr_type = "int"
    assert ident.expr_type == "int"
    # setting it on one node must not leak to others
    assert A.Identifier(name="y", **P).expr_type is None
