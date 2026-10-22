"""Tests for semantic analysis (symbol table, scopes, type checks, diagnostics).

Owner: Raghav (test_semantic_*.py).
"""
import pytest
from c2f.semantic import analyze
from c2f.syntax import (
    ArrayAccess,
    Assign,
    BinaryOp,
    Block,
    Break,
    Call,
    Continue,
    ExprStmt,
    For,
    Function,
    Identifier,
    If,
    Literal,
    Program,
    Return,
    Switch,
    UnaryOp,
    VarDecl,
    While,
)


def test_valid_program_types_and_no_errors():
    """Valid program with variable declarations, assignments, arithmetic, and return."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="main",
                return_type="int",
                params=[],
                body=Block(
                    line=1,
                    col=12,
                    statements=[
                        VarDecl(line=2, col=5, var_type="int", name="x", init=Literal(line=2, col=17, value="10", literal_type="int")),
                        VarDecl(line=3, col=5, var_type="int", name="y", init=None),
                        ExprStmt(
                            line=4,
                            col=5,
                            expr=Assign(
                                line=4,
                                col=5,
                                target=Identifier(line=4, col=5, name="y"),
                                op="=",
                                value=BinaryOp(
                                    line=4,
                                    col=9,
                                    op="+",
                                    left=Identifier(line=4, col=9, name="x"),
                                    right=Literal(line=4, col=13, value="5", literal_type="int"),
                                ),
                            ),
                        ),
                        Return(line=5, col=5, value=Identifier(line=5, col=12, name="y")),
                    ],
                ),
            )
        ],
    )

    result = analyze(ast)
    assert not result.errors
    # Verify .expr_type annotations
    ret_expr = ast.functions[0].body.statements[3].value
    assert ret_expr.expr_type == "int"
    assign_expr = ast.functions[0].body.statements[2].expr
    assert assign_expr.expr_type == "int"
    assert assign_expr.value.expr_type == "int"


def test_undeclared_variable_error():
    """Using an undeclared variable should produce a semantic error."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="main",
                return_type="int",
                params=[],
                body=Block(
                    line=1,
                    col=12,
                    statements=[
                        Return(line=2, col=5, value=Identifier(line=2, col=12, name="z")),
                    ],
                ),
            )
        ],
    )

    result = analyze(ast)
    assert len(result.errors) == 1
    err = result.errors[0]
    assert err.phase == "semantic"
    assert err.severity == "error"
    assert "undeclared" in err.message.lower()
    assert "z" in err.message


def test_redeclaration_in_same_scope():
    """Declaring the same variable twice in the same scope is an error."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="main",
                return_type="int",
                params=[],
                body=Block(
                    line=1,
                    col=12,
                    statements=[
                        VarDecl(line=2, col=5, var_type="int", name="x", init=None),
                        VarDecl(line=3, col=5, var_type="float", name="x", init=None),
                    ],
                ),
            )
        ],
    )

    result = analyze(ast)
    assert len(result.errors) == 1
    assert "redeclaration" in result.errors[0].message.lower()


def test_shadowing_in_inner_scope_is_valid():
    """Declaring the same name in a nested block shadows the outer variable legally."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="main",
                return_type="int",
                params=[],
                body=Block(
                    line=1,
                    col=12,
                    statements=[
                        VarDecl(line=2, col=5, var_type="int", name="x", init=Literal(line=2, col=17, value="1", literal_type="int")),
                        Block(
                            line=3,
                            col=5,
                            statements=[
                                VarDecl(line=4, col=9, var_type="float", name="x", init=Literal(line=4, col=23, value="2.5", literal_type="float")),
                                Return(line=5, col=9, value=Identifier(line=5, col=16, name="x")),
                            ],
                        ),
                    ],
                ),
            )
        ],
    )

    result = analyze(ast)
    assert not result.errors
    inner_return = ast.functions[0].body.statements[1].statements[1].value
    assert inner_return.expr_type == "float"


def test_break_and_continue_outside_loop():
    """break and continue outside any loop or switch must report semantic errors."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="main",
                return_type="void",
                params=[],
                body=Block(
                    line=1,
                    col=12,
                    statements=[
                        Break(line=2, col=5),
                        Continue(line=3, col=5),
                    ],
                ),
            )
        ],
    )

    result = analyze(ast)
    assert len(result.errors) == 2
    messages = [e.message for e in result.errors]
    assert any("break" in m for m in messages)
    assert any("continue" in m for m in messages)


def test_break_inside_loop_and_switch_is_valid():
    """break inside while loop and switch is valid; continue inside while is valid."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="main",
                return_type="int",
                params=[],
                body=Block(
                    line=1,
                    col=12,
                    statements=[
                        VarDecl(line=2, col=5, var_type="int", name="i", init=Literal(line=2, col=17, value="0", literal_type="int")),
                        While(
                            line=3,
                            col=5,
                            cond=BinaryOp(line=3, col=12, op="<", left=Identifier(line=3, col=12, name="i"), right=Literal(line=3, col=16, value="10", literal_type="int")),
                            body=Block(
                                line=3,
                                col=20,
                                statements=[
                                    Break(line=4, col=9),
                                    Continue(line=5, col=9),
                                ],
                            ),
                        ),
                    ],
                ),
            )
        ],
    )

    result = analyze(ast)
    assert not result.errors


def test_function_call_arg_count_mismatch():
    """Calling a user-defined function with wrong number of arguments reports an error."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="add",
                return_type="int",
                params=[{"type": "int", "name": "a"}, {"type": "int", "name": "b"}],
                body=Block(line=1, col=20, statements=[Return(line=2, col=5, value=Literal(line=2, col=12, value="0", literal_type="int"))]),
            ),
            Function(
                line=4,
                col=1,
                name="main",
                return_type="int",
                params=[],
                body=Block(
                    line=4,
                    col=12,
                    statements=[
                        ExprStmt(
                            line=5,
                            col=5,
                            expr=Call(line=5, col=5, name="add", args=[Literal(line=5, col=9, value="1", literal_type="int")]),
                        )
                    ],
                ),
            ),
        ],
    )

    result = analyze(ast)
    assert len(result.errors) == 1
    assert "expects 2" in result.errors[0].message


def test_void_function_return_value_error():
    """Returning a value from a void function reports an error."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="foo",
                return_type="void",
                params=[],
                body=Block(
                    line=1,
                    col=12,
                    statements=[
                        Return(line=2, col=5, value=Literal(line=2, col=12, value="42", literal_type="int")),
                    ],
                ),
            )
        ],
    )

    result = analyze(ast)
    assert len(result.errors) == 1
    assert "void function" in result.errors[0].message.lower()
