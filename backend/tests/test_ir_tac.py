"""TAC data model + fixture contract checks. Owner: Raghav."""
import pytest

from c2f.ir import TacInstr, TacProgram, is_literal

CONTRACT_KEYS = ["id", "op", "result", "arg1", "arg2", "operator", "target", "label", "args", "line", "src"]


@pytest.mark.parametrize("text", ["5", "-5", "3.5", ".5", "'a'", "'\\n'", '"hi"', '"%d"', '""'])
def test_is_literal_true(text):
    assert is_literal(text)


@pytest.mark.parametrize("text", ["x", "t1", "n", "&n", "a+b", "5x", "'ab'", '"open'])
def test_is_literal_false(text):
    assert not is_literal(text)


def test_unknown_op_rejected():
    with pytest.raises(ValueError):
        TacInstr(1, "nop")


def test_binop_needs_valid_operator():
    with pytest.raises(ValueError):
        TacInstr(1, "binop", result="t1", arg1="a", arg2="b", operator="**")
    TacInstr(1, "binop", result="t1", arg1="a", arg2="b", operator="+")


def test_label_goto_and_call_required_fields():
    with pytest.raises(ValueError):
        TacInstr(1, "label")
    with pytest.raises(ValueError):
        TacInstr(1, "goto")
    with pytest.raises(ValueError):
        TacInstr(1, "if_false", arg1="t1")
    with pytest.raises(ValueError):
        TacInstr(1, "call")


def test_to_dict_has_every_contract_key_in_order():
    d = TacInstr(3, "return", arg1="0", line=9, src="return 0").to_dict()
    assert list(d) == CONTRACT_KEYS
    assert d["args"] == [] and d["result"] is None


def test_instr_roundtrip():
    i = TacInstr(7, "call", arg1="printf", args=['"%d"', "b"], line=5, src='printf("%d", b)')
    assert TacInstr.from_dict(i.to_dict()) == i


def _all_tac(load_fixture):
    gen = load_fixture("generate_ok")["data"]
    opt = load_fixture("optimize_ok")["data"]
    return [gen["tac"], opt["original"]["tac"], opt["optimized"]["tac"]]


def test_fixture_tac_loads_and_roundtrips(load_fixture):
    for tac in _all_tac(load_fixture):
        assert TacProgram.from_dict(tac).to_dict() == tac


def test_fixture_tac_contract_rules(load_fixture):
    for tac in _all_tac(load_fixture):
        prog = TacProgram.from_dict(tac)
        for fn in prog.functions.values():
            ids = [i.id for i in fn.instrs]
            assert len(ids) == len(set(ids)), "ids must be unique"
            assert fn.instrs[-1].op == "return", "every function ends with an explicit return"
            defined = {i.label for i in fn.instrs if i.op == "label"}
            for i in fn.instrs:
                if i.target:
                    assert i.target in defined, f"jump to undefined label {i.target}"
            for i in fn.instrs:
                if i.result and i.op != "array_store":
                    assert not is_literal(i.result)


def test_next_id():
    prog = TacProgram.from_dict({"main": [TacInstr(4, "return", arg1="0").to_dict()]})
    assert prog.next_id() == 5
    assert TacProgram().next_id() == 1
