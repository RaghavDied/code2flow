
import pytest

from c2f.ir import TacFunction, TacInstr, TacProgram
from c2f.optimizer import tac_to_c


def instr(id, op, **kwargs):
    return TacInstr(id=id, op=op, **kwargs)


def test_generates_function_with_assignment_and_return():
    program = TacProgram({
        "main": TacFunction(
            "main",
            [],
            [
                instr(1, "assign", result="x", arg1="5"),
                instr(2, "return", arg1="x"),
            ],
        )
    })

    source = tac_to_c(program)

    assert "#include <stdio.h>" in source
    assert "int main(void) {" in source
    assert "int x;" in source
    assert "x = 5;" in source
    assert "return x;" in source


def test_generates_arithmetic_and_unary_operations():
    program = TacProgram({
        "main": TacFunction(
            "main",
            [],
            [
                instr(1, "binop", result="t1", arg1="2", arg2="3",
                      operator="+"),
                instr(2, "unop", result="t2", arg1="t1", operator="-"),
                instr(3, "return", arg1="t2"),
            ],
        )
    })

    source = tac_to_c(program)

    assert "t1 = (2 + 3);" in source
    assert "t2 = (-t1);" in source
    assert "return t2;" in source


def test_generates_conditional_branches_and_labels():
    program = TacProgram({
        "main": TacFunction(
            "main",
            [],
            [
                instr(1, "if_false", arg1="x", target="L0"),
                instr(2, "goto", target="L1"),
                instr(3, "label", label="L0"),
                instr(4, "label", label="L1"),
                instr(5, "return", arg1="0"),
            ],
        )
    })

    source = tac_to_c(program)

    assert "if (!(x)) goto L0;" in source
    assert "goto L1;" in source
    assert "L0: ;" in source
    assert "L1: ;" in source


def test_generates_function_calls_and_address_arguments():
    program = TacProgram({
        "main": TacFunction(
            "main",
            [],
            [
                instr(1, "call", arg1="scanf", args=['"%d"', "&x"]),
                instr(2, "call", arg1="printf", args=['"%d"', "x"]),
                instr(3, "return", arg1="0"),
            ],
        )
    })

    source = tac_to_c(program)

    assert 'scanf("%d", &x);' in source
    assert 'printf("%d", x);' in source
    assert "int x;" in source


def test_rejects_array_operations_until_supported():
    program = TacProgram({
        "main": TacFunction(
            "main",
            [],
            [instr(1, "array_load", result="x", arg1="arr", arg2="0")],
        )
    })

    with pytest.raises(NotImplementedError, match="array_load"):
        tac_to_c(program)


def test_rejects_invalid_identifiers():
    program = TacProgram({
        "main": TacFunction(
            "main",
            [],
            [instr(1, "assign", result="x; system", arg1="1")],
        )
    })

    with pytest.raises(ValueError, match="Invalid C identifier"):
        tac_to_c(program)
