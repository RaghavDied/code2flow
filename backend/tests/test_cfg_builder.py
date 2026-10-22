"""Unit tests for CFG builder, basic blocks, dominators, and loop detection.

Owner: Raghav (test_cfg_*.py).
"""
import pytest
from c2f.cfg import build_cfg, cfg_to_dict
from c2f.cfg.basic_blocks import partition_into_basic_blocks
from c2f.cfg.dominators import compute_dominators, compute_immediate_dominators
from c2f.cfg.loops import find_back_edges
from c2f.ir import TacFunction, TacInstr, generate_tac
from c2f.metrics import compute_metrics
from c2f.syntax import (
    BinaryOp,
    Block,
    Call,
    ExprStmt,
    Function,
    Identifier,
    If,
    Literal,
    Program,
    Return,
    VarDecl,
    While,
)


def test_linear_cfg():
    """Simple linear function should have START (B0), one process block, and END."""
    instrs = [
        TacInstr(id=1, op="assign", result="x", arg1="10", line=2, src="int x = 10"),
        TacInstr(id=2, op="return", arg1="x", line=3, src="return x"),
    ]
    fn = TacFunction(name="main", params=[], instrs=instrs)
    cfg = build_cfg(fn)

    assert len(cfg.nodes) == 3
    assert cfg.nodes[0].id == "B0"
    assert cfg.nodes[0].type == "start"
    assert cfg.nodes[1].id == "B1"
    assert cfg.nodes[1].type == "process"
    assert cfg.nodes[2].id == "B2"
    assert cfg.nodes[2].type == "end"

    # Edges B0 -> B1 -> B2
    assert len(cfg.edges) == 2
    assert cfg.edges[0].source == "B0" and cfg.edges[0].target == "B1"
    assert cfg.edges[1].source == "B1" and cfg.edges[1].target == "B2"


def test_io_node_detection():
    """A block whose only work is printf or scanf calls must have type 'io'."""
    instrs = [
        TacInstr(id=1, op="call", arg1="printf", args=['"hello"'], line=2, src='printf("hello")'),
        TacInstr(id=2, op="goto", target="L0", line=2, src="goto L0"),
        TacInstr(id=3, op="label", label="L0", line=3, src="L0:"),
        TacInstr(id=4, op="return", line=3, src="return"),
    ]
    fn = TacFunction(name="greet", params=[], instrs=instrs)
    cfg = build_cfg(fn)
    # B1 has only printf, so it should be "io"
    b1 = cfg.node("B1")
    assert b1.type == "io"
    # B2 has return, so it is "process"
    b2 = cfg.node("B2")
    assert b2.type == "process"


def test_if_else_branching_and_decisions():
    """Decision node ending in '?' with TRUE and FALSE edges."""
    # L0 is else, L1 is end
    instrs = [
        TacInstr(id=1, op="binop", result="t1", arg1="x", operator=">", arg2="0", line=3, src="x > 0"),
        TacInstr(id=2, op="if_false", arg1="t1", target="L0", line=3, src="x > 0"),
        TacInstr(id=3, op="call", arg1="printf", args=['"pos"'], line=4, src='printf("pos")'),
        TacInstr(id=4, op="goto", target="L1", line=4, src="goto L1"),
        TacInstr(id=5, op="label", label="L0", line=5, src="L0:"),
        TacInstr(id=6, op="call", arg1="printf", args=['"neg"'], line=6, src='printf("neg")'),
        TacInstr(id=7, op="label", label="L1", line=7, src="L1:"),
        TacInstr(id=8, op="return", line=7, src="return"),
    ]
    fn = TacFunction(name="test_if", params=["x"], instrs=instrs)
    cfg = build_cfg(fn)

    # Find decision node
    decision_nodes = [n for n in cfg.nodes if n.type == "decision"]
    assert len(decision_nodes) == 1
    d_node = decision_nodes[0]
    assert d_node.label.endswith("?")

    # Decision node must have exactly 2 outgoing edges: TRUE and FALSE
    out = cfg.out_edges(d_node.id)
    assert len(out) == 2
    labels = {e.label for e in out}
    assert labels == {"TRUE", "FALSE"}


def test_while_loop_back_edge_and_loop_header():
    """While loop must have a back edge and the target marked as loop header."""
    instrs = [
        TacInstr(id=1, op="assign", result="i", arg1="0", line=2, src="int i = 0"),
        TacInstr(id=2, op="label", label="L0", line=3, src="L0:"),
        TacInstr(id=3, op="binop", result="t1", arg1="i", operator="<", arg2="3", line=3, src="i < 3"),
        TacInstr(id=4, op="if_false", arg1="t1", target="L1", line=3, src="i < 3"),
        TacInstr(id=5, op="call", arg1="printf", args=["i"], line=4, src="printf(i)"),
        TacInstr(id=6, op="goto", target="L0", line=5, src="goto L0"),
        TacInstr(id=7, op="label", label="L1", line=6, src="L1:"),
        TacInstr(id=8, op="return", line=6, src="return"),
    ]
    fn = TacFunction(name="loop_fn", params=[], instrs=instrs)
    cfg = build_cfg(fn)

    back_edges = [e for e in cfg.edges if e.is_back_edge]
    assert len(back_edges) == 1

    # Loop header node
    header = cfg.node(back_edges[0].target)
    assert header.is_loop_header is True

    # Compute metrics
    metrics = compute_metrics(cfg)
    assert metrics["loops"] == 1
    assert metrics["decisions"] >= 1
    assert metrics["cyclomatic_complexity"] == metrics["edges"] - metrics["nodes"] + 2


def test_dominators_computation():
    """Verify dominators calculation on a structured CFG."""
    instrs = [
        TacInstr(id=1, op="assign", result="a", arg1="1", line=2, src="int a = 1"),
        TacInstr(id=2, op="return", line=3, src="return"),
    ]
    fn = TacFunction(name="dom_test", params=[], instrs=instrs)
    cfg = build_cfg(fn)
    doms = compute_dominators(cfg)

    # B0 must dominate all reachable nodes
    assert "B0" in doms["B0"]
    assert "B0" in doms["B1"]
    assert "B0" in doms["B2"]

    idoms = compute_immediate_dominators(cfg)
    assert idoms["B0"] is None
    assert idoms["B1"] == "B0"
    assert idoms["B2"] == "B1"


def test_ast_to_cfg_end_to_end():
    """End-to-end integration: AST -> generate_tac -> build_cfg -> compute_metrics."""
    ast = Program(
        line=1,
        col=1,
        functions=[
            Function(
                line=1,
                col=1,
                name="max",
                return_type="int",
                params=[{"type": "int", "name": "a"}, {"type": "int", "name": "b"}],
                body=Block(
                    line=1,
                    col=20,
                    statements=[
                        If(
                            line=2,
                            col=5,
                            cond=BinaryOp(line=2, col=9, op=">", left=Identifier(line=2, col=9, name="a"), right=Identifier(line=2, col=13, name="b")),
                            then=Return(line=3, col=9, value=Identifier(line=3, col=16, name="a")),
                            else_=Return(line=5, col=9, value=Identifier(line=5, col=16, name="b")),
                        )
                    ],
                ),
            )
        ],
    )

    tac_prog = generate_tac(ast)
    assert "max" in tac_prog.functions
    cfg = build_cfg(tac_prog.functions["max"])

    d = cfg_to_dict(cfg)
    assert d["function"] == "max"
    assert any(n["type"] == "start" for n in d["nodes"])
    assert any(n["type"] == "end" for n in d["nodes"])
    assert any(n["type"] == "decision" for n in d["nodes"])

    metrics = compute_metrics(cfg)
    assert metrics["decisions"] == 1
    assert metrics["cyclomatic_complexity"] >= 1
