
"""End-to-end tests for Ishani's TAC-to-C converter."""
import shutil
import subprocess

import pytest

from c2f.ir import TacFunction, TacInstr, TacProgram
from c2f.optimizer.tac_to_c import tac_to_c


def make_program(instructions):
    function = TacFunction(name="main", params=[], instrs=instructions)
    return TacProgram(functions={"main": function})


def compile_and_run(tmp_path, source):
    """Compile generated C and return the executable's exit code."""
    compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        pytest.skip("No C compiler (cc, gcc, or clang) available")

    c_file = tmp_path / "generated.c"
    executable = tmp_path / "generated"
    c_file.write_text(source, encoding="utf-8")

    subprocess.run(
        [compiler, "-std=c11", "-Wall", "-Werror", str(c_file), "-o", str(executable)],
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run([str(executable)], check=False, capture_output=True)
    return result.returncode


def test_generated_c_executes_arithmetic_program(tmp_path):
    program = make_program([
        TacInstr(id=0, op="binop", result="t1", arg1="2", arg2="3", operator="+"),
        TacInstr(id=1, op="assign", result="answer", arg1="t1"),
        TacInstr(id=2, op="return", arg1="answer"),
    ])

    generated_c = tac_to_c(program)

    assert "int main(void)" in generated_c
    assert compile_and_run(tmp_path, generated_c) == 5


def test_generated_c_executes_conditional_branch(tmp_path):
    program = make_program([
        TacInstr(id=0, op="assign", result="x", arg1="0"),
        TacInstr(id=1, op="if_false", arg1="x", target="L0"),
        TacInstr(id=2, op="assign", result="answer", arg1="1"),
        TacInstr(id=3, op="goto", target="L1"),
        TacInstr(id=4, op="label", label="L0"),
        TacInstr(id=5, op="assign", result="answer", arg1="2"),
        TacInstr(id=6, op="label", label="L1"),
        TacInstr(id=7, op="return", arg1="answer"),
    ])

    generated_c = tac_to_c(program)

    assert "if (!(x)) goto L0;" in generated_c
    assert compile_and_run(tmp_path, generated_c) == 2
