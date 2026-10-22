"""
test_optimizer_passes.py (Ishani)

Tests the 6 core passes individually, the fixed-point optimize() pipeline,
and -- most importantly -- the project's correctness rule (doc section 5):
"an optimisation must never change program behaviour", checked by running
interpret() on a program before and after optimize() and comparing output.
"""
import copy
import pathlib

import pytest

from _fixture_loader import load_tac_program
from c2f.optimizer import algebraic, branch_simplify, const_prop, constant_fold, dead_code, unreachable
from c2f.optimizer.manager import optimize
from c2f.optimizer.interpreter import _Interpreter, interpret
from c2f.optimizer._support import render

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "tac"


def load(name):
    return load_tac_program(str(FIXTURES / f"{name}.json"))


def by_id(fn, instr_id):
    return next(i for i in fn.instrs if i.id == instr_id)


# ------------------------------------------------------- individual passes ---

def test_constant_fold_binop():
    fn = load("constant_folding_basic").functions["main"]
    log = constant_fold.run(fn)
    assert render(by_id(fn, 1)) == "t1 = 6"
    assert len(log) == 1
    assert log[0].pass_name == "constant_folding"
    assert log[0].before == "t1 = 2 * 3"
    assert log[0].after == "t1 = 6"


def test_algebraic_simplification_identities():
    fn = load("algebraic_simplification_basic").functions["main"]
    log = algebraic.run(fn)
    assert render(by_id(fn, 1)) == "x = y"
    assert render(by_id(fn, 2)) == "z = y"
    assert len(log) == 2


def test_constant_propagation_substitutes_literal():
    fn = load("constant_propagation_basic").functions["main"]
    const_prop.run(fn)
    assert render(by_id(fn, 2)) == "y = 5 + 1"


def test_dead_code_elimination_removes_unused_assign():
    fn = load("dead_code_basic").functions["main"]
    dead_code.run(fn)
    assert [i.id for i in fn.instrs] == [2]


def test_dead_code_elimination_keeps_live_assign_in_loop():
    fn = load("loop_with_dead_var").functions["main"]
    dead_code.run(fn)
    ids = {i.id for i in fn.instrs}
    assert 5 not in ids  # junk = 7, dead
    assert 7 in ids      # i = i+1, live (feeds the loop condition)


def test_branch_simplify_removes_if_false_that_never_branches():
    fn = load("branch_always_true").functions["main"]
    constant_fold.run(fn)
    const_prop.run(fn)
    branch_simplify.run(fn)
    assert 2 not in [i.id for i in fn.instrs]


def test_branch_simplify_converts_if_false_that_always_branches_to_goto():
    fn = load("branch_always_false").functions["main"]
    constant_fold.run(fn)
    const_prop.run(fn)
    branch_simplify.run(fn)
    instr2 = by_id(fn, 2)
    assert instr2.op == "goto"
    assert instr2.target == "L0"


def test_unreachable_removes_code_after_return():
    fn = load("unreachable_after_return").functions["main"]
    unreachable.run(fn)
    assert [i.id for i in fn.instrs] == [1, 2]


# -------------------------------------------------------------- optimize() ---

def test_optimize_does_not_mutate_its_input():
    original = load("constant_folding_basic")
    original_ids_before = [i.id for i in original.functions["main"].instrs]
    original_ops_before = [i.op for i in original.functions["main"].instrs]
    optimize(original)
    assert [i.id for i in original.functions["main"].instrs] == original_ids_before
    assert [i.op for i in original.functions["main"].instrs] == original_ops_before


def test_optimize_worked_example_collapses_dead_branch_and_unused_var():
    # Combined worked example from the project doc section 5: a=2*3, b=a+4,
    # unused=99, if(1){printf(b)}else{printf(never)}, return 0.
    result = optimize(load("combined_worked_example"))
    fn = result.program.functions["main"]
    remaining_src = {i.src for i in fn.instrs}
    assert not any("unused" in s for s in remaining_src)
    assert not any("never" in s for s in remaining_src)
    assert len(result.log) > 0


# --------------------------------------- correctness rule: behaviour preserved ---

@pytest.mark.parametrize(
    "fixture_name,inputs",
    [
        ("constant_folding_basic", []),
        ("dead_code_basic", []),
        ("branch_always_true", []),
        ("branch_always_false", []),
        ("combined_worked_example", []),
        ("unreachable_after_return", []),
        ("constant_propagation_basic", []),
        ("io_scanf_basic", ["5"]),
    ],
)
def test_optimize_preserves_behaviour_zero_arg_main(fixture_name, inputs):
    original = load(fixture_name)
    before = interpret(copy.deepcopy(original), inputs)
    result = optimize(original)
    after = interpret(result.program, inputs)
    assert before == after, f"{fixture_name}: optimisation changed program output!"


@pytest.mark.parametrize(
    "fixture_name,args",
    [
        ("loop_with_dead_var", [0]),
        ("loop_with_dead_var", [1]),
        ("loop_with_dead_var", [2]),
        ("loop_with_dead_var", [5]),
        ("loop_with_dead_var", [10]),
        ("algebraic_simplification_basic", [-5]),
        ("algebraic_simplification_basic", [0]),
        ("algebraic_simplification_basic", [5]),
    ],
)
def test_optimize_preserves_behaviour_main_with_params(fixture_name, args):
    original = load(fixture_name)
    before = _Interpreter(copy.deepcopy(original), []).run("main", args)
    result = optimize(original)
    after = _Interpreter(result.program, []).run("main", args)
    assert before == after, f"{fixture_name}: optimisation changed return value!"
