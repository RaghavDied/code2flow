"""
test_optimizer_interpreter.py (Ishani)

Runs the interpreter against hand-made fixtures and checks the captured
printf output. This is the same mechanism every optimisation pass's test
will use: interpret(original, inputs) == interpret(optimised, inputs).
"""
import pathlib

from c2f.optimizer.interpreter import interpret
from _fixture_loader import load_tac_program

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "tac"


def load(name):
    return load_tac_program(str(FIXTURES / f"{name}.json"))


def test_constant_folding_fixture_returns_folded_value():
    # t1 = 2*3; return t1  -- no printf output, but must not raise.
    prog = load("constant_folding_basic")
    assert interpret(prog, []) == []


def test_combined_worked_example_prints_b_not_never():
    # a=2*3, b=a+4=10; if(1) printf("%d", b) else printf("never")
    prog = load("combined_worked_example")
    assert interpret(prog, []) == ["10"]


def test_branch_always_true_takes_then_branch():
    prog = load("branch_always_true")
    assert interpret(prog, []) == ["then"]


def test_branch_always_false_skips_then_branch():
    prog = load("branch_always_false")
    assert interpret(prog, []) == []


def test_loop_with_dead_var_runs_to_completion():
    # while (i < n) { junk = 7; i = i+1; } return i;  -- n is a param, not set here,
    # so bind it directly via the interpreter's function-call entry point.
    from c2f.optimizer.interpreter import _Interpreter

    prog = load("loop_with_dead_var")
    interp = _Interpreter(prog, [])
    result = interp.run("main", [3])
    assert result == 3


def test_scanf_reads_input_and_printf_reports_computed_value():
    prog = load("io_scanf_basic")
    # x = 5 (from inputs), y = x*2 = 10, printf("%d", y)
    assert interpret(prog, ["5"]) == ["10"]


def test_unreachable_after_return_only_prints_nothing_and_returns_first_value():
    from c2f.optimizer.interpreter import _Interpreter

    prog = load("unreachable_after_return")
    interp = _Interpreter(prog, [])
    result = interp.run("main", [])
    assert result == 1  # returns x (=1) at instr 2, never reaches y=2/return y
