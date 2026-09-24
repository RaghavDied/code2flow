"""
test_optimizer_dataflow.py (Ishani)

Unit tests for c2f/optimizer/dataflow.py: def/use extraction, successor/
predecessor graphs, reaching definitions and live-variable analysis --
checked against the hand-made fixtures in backend/tests/fixtures/tac/.
"""
import pathlib

import pytest

from c2f.optimizer.dataflow import (
    LiveVariables,
    ReachingDefinitions,
    def_use,
    predecessors,
    successors,
)
from c2f.optimizer._tac_contract_stub import load_tac_program

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "tac"


def load(name):
    prog = load_tac_program(str(FIXTURES / f"{name}.json"))
    return prog.functions["main"]


def by_id(fn, instr_id):
    return next(i for i in fn.instrs if i.id == instr_id)


# ---------------------------------------------------------------- def_use ---

def test_def_use_binop():
    fn = load("constant_folding_basic")
    defs, uses = def_use(by_id(fn, 1))  # t1 = 2 * 3
    assert defs == {"t1"}
    assert uses == set()  # both operands are literals


def test_def_use_assign_with_variable():
    fn = load("copy_propagation_basic")
    defs, uses = def_use(by_id(fn, 1))  # a = b
    assert defs == {"a"}
    assert uses == {"b"}


def test_def_use_if_false_uses_condition_var():
    fn = load("loop_with_dead_var")
    defs, uses = def_use(by_id(fn, 4))  # if_false t1 goto L1
    assert defs == set()
    assert uses == {"t1"}


def test_def_use_call_uses_args_ignores_string_literal():
    fn = load("combined_worked_example")
    defs, uses = def_use(by_id(fn, 8))  # call printf("%d", b)
    assert defs == set()
    assert uses == {"b"}  # the format-string literal is not a variable use


# ------------------------------------------------------- successors/preds ---

def test_successors_linear_block_falls_through():
    fn = load("constant_propagation_basic")  # x=5; y=x+1; return y  (no jumps)
    succ = successors(fn)
    assert succ[1] == [2]
    assert succ[2] == [3]
    assert succ[3] == []  # return has no successor


def test_successors_if_false_has_two_targets():
    fn = load("branch_always_true")
    succ = successors(fn)
    # instr 2 is `if_false t1 goto L0`: fallthrough to instr 3, jump to the L0 label (instr 5)
    assert succ[2] == [3, 5]


def test_successors_goto_back_edge_in_loop():
    fn = load("loop_with_dead_var")
    succ = successors(fn)
    # instr 8 is `goto L0`, L0 is the label at instr 2
    assert succ[8] == [2]


def test_predecessors_is_inverse_of_successors():
    fn = load("loop_with_dead_var")
    succ = successors(fn)
    pred = predecessors(fn)
    for src, targets in succ.items():
        for t in targets:
            assert src in pred[t]


# ------------------------------------------------------ reaching definitions ---

def test_reaching_definitions_constant_propagation_fixture():
    fn = load("constant_propagation_basic")  # 1: x=5  2: y=x+1  3: return y
    result = ReachingDefinitions(fn).solve()
    use_instr = by_id(fn, 2)
    reaching = result.reaching_at_use(use_instr, "x")
    assert reaching == {1}, "x used in instr 2 must be reached only by the def at instr 1"


def test_reaching_definitions_respects_redefinition():
    fn = load("loop_with_dead_var")
    # i is defined at instr 1 (i=0) and redefined at instr 7 (i = t2) inside the loop body.
    result = ReachingDefinitions(fn).solve()
    # the use of i in the loop condition (instr 3: t1 = i < n) can be reached by EITHER
    # the initial def (1) on the first iteration or the redef (7) on later iterations.
    reaching = result.reaching_at_use(by_id(fn, 3), "i")
    assert reaching == {1, 7}


# ---------------------------------------------------------- live variables ---

def test_liveness_flags_dead_assignment():
    fn = load("dead_code_basic")  # 1: x=4 (never read)  2: return 0
    result = LiveVariables(fn).solve()
    assert result.is_dead_assignment(by_id(fn, 1), "x") is True


def test_liveness_keeps_used_assignment_live():
    fn = load("constant_propagation_basic")  # 1: x=5  2: y=x+1 (uses x)  3: return y
    result = LiveVariables(fn).solve()
    assert result.is_dead_assignment(by_id(fn, 1), "x") is False


def test_liveness_flags_dead_assignment_inside_loop_body():
    fn = load("loop_with_dead_var")  # instr 5: junk = 7, never read anywhere
    result = LiveVariables(fn).solve()
    assert result.is_dead_assignment(by_id(fn, 5), "junk") is True
    # but i (defined at instr 7) IS live -- it feeds the loop condition on the next iteration
    assert result.is_dead_assignment(by_id(fn, 7), "i") is False


def test_liveness_return_value_is_live_before_return():
    fn = load("dead_code_basic")
    result = LiveVariables(fn).solve()
    return_instr = by_id(fn, 2)
    assert "x" not in result.in_sets[return_instr.id]  # x isn't used by `return 0`


@pytest.mark.parametrize(
    "fixture,instr_id,var",
    [
        ("cse_basic", 1, "a"),      # t1 = a + b; a is used again at instr 2
        ("cse_basic", 1, "b"),
    ],
)
def test_liveness_operands_reused_in_next_instr_stay_live(fixture, instr_id, var):
    fn = load(fixture)
    result = LiveVariables(fn).solve()
    instr = by_id(fn, instr_id)
    assert var in result.out_sets[instr.id]
