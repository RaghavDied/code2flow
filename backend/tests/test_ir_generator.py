"""Unit tests for TAC IR generator (c2f/ir/tac_generator.py).

Owner: Raghav (test_ir_*.py).
"""
import pytest
from c2f.ir import generate_tac, is_literal
from c2f.semantic.ast_nodes import (
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
    Program,
    Return,
    Switch,
    UnaryOp,
    VarDecl,
    While,
)


def test_generate_tac_basic_arithmetic():
    """Test generating TAC for variable declarations, assignments, and arithmetic."""
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
                        VarDecl(line=2, col=5, var_type="int", name="a", init=Literal(line=2, col=17, value="2", literal_type="int")),
                        VarDecl(line=3, col=5, var_type="int", name="b", init=Literal(line=3, col=17, value="3", literal_type="int")),
                        VarDecl(
                            line=4,
                            col=5,
                            var_type="int",
                            name="c",
                            init=BinaryOp(
                                line=4,
                                col=17,
                                op="+",
                                left=Identifier(line=4, col=17, name="a"),
                                right=Identifier(line=4, col=21, name="b"),
                            ),
                        ),
                        Return(line=5, col=5, value=Identifier(line=5, col=12, name="c")),
                    ],
                ),
            )
        ],
    )

    prog = generate_tac(ast)
    assert "main" in prog.functions
    fn = prog.functions["main"]
    ops = [i.op for i in fn.instrs]

    assert "assign" in ops
    assert "binop" in ops
    assert "return" in ops
    # IDs must be unique and positive
    ids = [i.id for i in fn.instrs]
    assert len(ids) == len(set(ids))
    assert all(i > 0 for i in ids)


def test_generate_tac_if_else():
    """if/else lowering must emit if_false, then body, goto end, else label, else body, end label."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="check",
                return_type="void",
                params=[{"type": "int", "name": "x"}],
                body=Block(
                    line=1,
                    col=15,
                    statements=[
                        If(
                            line=2,
                            col=5,
                            cond=BinaryOp(line=2, col=9, op=">", left=Identifier(line=2, col=9, name="x"), right=Literal(line=2, col=13, value="0", literal_type="int")),
                            then=ExprStmt(line=3, col=9, expr=Call(line=3, col=9, name="printf", args=[Literal(line=3, col=16, value='"pos"', literal_type="string")])),
                            else_=ExprStmt(line=5, col=9, expr=Call(line=5, col=9, name="printf", args=[Literal(line=5, col=16, value='"neg"', literal_type="string")])),
                        )
                    ],
                ),
            )
        ],
    )

    prog = generate_tac(ast)
    fn = prog.functions["check"]
    assert fn.params == ["x"]
    ops = [i.op for i in fn.instrs]

    assert "if_false" in ops
    assert "goto" in ops
    assert "label" in ops
    assert ops.count("call") == 2
    assert ops[-1] == "return"


def test_generate_tac_while_with_break():
    """while loop must emit condition label, if_false, body with break goto, and end label."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="loop",
                return_type="void",
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
                                ],
                            ),
                        ),
                    ],
                ),
            )
        ],
    )

    prog = generate_tac(ast)
    fn = prog.functions["loop"]
    ops = [i.op for i in fn.instrs]

    assert "if_false" in ops
    # The break should emit a goto pointing to the end label of the loop
    break_gotos = [i for i in fn.instrs if i.op == "goto" and i.src == "break;"]
    assert len(break_gotos) == 1
    # Target of break goto must match the final label after the loop
    end_label = fn.instrs[-2]  # before explicit return
    assert end_label.op == "label"
    assert break_gotos[0].target == end_label.label


def test_generate_tac_for_loop():
    """for loop must emit init, cond label, if_false, body, update label, update, goto cond, end label."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="count",
                return_type="void",
                params=[],
                body=Block(
                    line=1,
                    col=12,
                    statements=[
                        For(
                            line=2,
                            col=5,
                            init=VarDecl(line=2, col=10, var_type="int", name="k", init=Literal(line=2, col=22, value="0", literal_type="int")),
                            cond=BinaryOp(line=2, col=25, op="<", left=Identifier(line=2, col=25, name="k"), right=Literal(line=2, col=29, value="5", literal_type="int")),
                            update=UnaryOp(line=2, col=32, op="++", operand=Identifier(line=2, col=32, name="k"), postfix=True),
                            body=Block(line=2, col=37, statements=[]),
                        )
                    ],
                ),
            )
        ],
    )

    prog = generate_tac(ast)
    fn = prog.functions["count"]
    ops = [i.op for i in fn.instrs]
    assert "assign" in ops
    assert "if_false" in ops
    assert "goto" in ops
    labels = [i.label for i in fn.instrs if i.op == "label"]
    assert len(labels) >= 3  # cond, update, end


def test_generate_tac_switch_fallthrough():
    """switch statement lowering to == binary operations and if_true jumps."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="switch_test",
                return_type="void",
                params=[{"type": "int", "name": "val"}],
                body=Block(
                    line=1,
                    col=20,
                    statements=[
                        Switch(
                            line=2,
                            col=5,
                            expr=Identifier(line=2, col=13, name="val"),
                            cases=[
                                Case(line=3, col=9, value=Literal(line=3, col=14, value="1", literal_type="int"), body=[Break(line=3, col=17)]),
                                Case(line=4, col=9, value=None, body=[]),  # default
                            ],
                        )
                    ],
                ),
            )
        ],
    )

    prog = generate_tac(ast)
    fn = prog.functions["switch_test"]
    ops = [i.op for i in fn.instrs]
    assert "if_true" in ops
    assert "goto" in ops


def test_generate_tac_array_access():
    """Array load and store must use array_load and array_store ops."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="arr_fn",
                return_type="int",
                params=[],
                body=Block(
                    line=1,
                    col=12,
                    statements=[
                        VarDecl(line=2, col=5, var_type="int", name="arr", array_size=10, init=None),
                        ExprStmt(
                            line=3,
                            col=5,
                            expr=Assign(
                                line=3,
                                col=5,
                                target=ArrayAccess(line=3, col=5, name="arr", index=Literal(line=3, col=9, value="0", literal_type="int")),
                                op="=",
                                value=Literal(line=3, col=14, value="42", literal_type="int"),
                            ),
                        ),
                        Return(
                            line=4,
                            col=5,
                            value=ArrayAccess(line=4, col=12, name="arr", index=Literal(line=4, col=16, value="0", literal_type="int")),
                        ),
                    ],
                ),
            )
        ],
    )

    prog = generate_tac(ast)
    fn = prog.functions["arr_fn"]
    ops = [i.op for i in fn.instrs]
    assert "array_store" in ops
    assert "array_load" in ops
