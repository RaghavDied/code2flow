"""
Sanity tests for backend/tests/fixtures/tac/*.json.

These do NOT test the optimiser itself (manager.py / passes don't exist yet).
They just guarantee every hand-written fixture is well-formed TacProgram JSON
per CONTRACTS.md section 6, so nothing downstream chokes on a malformed
fixture later. Once c2f.optimizer.optimize() exists, add
test_optimizer_passes.py (one test per pass) that loads these fixtures,
calls optimize(), and asserts on the resulting instrs + log, using
interpret() to prove input/output TAC behave identically.
"""
import json
import pathlib

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures" / "tac"

VALID_OPS = {
    "assign", "binop", "unop", "label", "goto", "if_false", "if_true",
    "call", "return", "array_load", "array_store",
}

INSTR_FIELDS = {
    "id", "op", "result", "arg1", "arg2", "operator", "target", "label",
    "args", "line", "src",
}


def _fixture_files():
    files = sorted(FIXTURES_DIR.glob("*.json"))
    files = [f for f in files if f.name != "MANIFEST.json"]
    assert len(files) >= 10, "expected at least 10 hand-made TAC fixtures"
    return files


@pytest.fixture(scope="module")
def manifest():
    with open(FIXTURES_DIR / "MANIFEST.json") as f:
        return json.load(f)


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.stem)
def test_fixture_matches_tac_contract(path):
    with open(path) as f:
        data = json.load(f)

    assert set(data.keys()) == {"functions"}
    assert data["functions"], "at least one function"

    seen_ids_by_fn = {}
    for fn_name, fn in data["functions"].items():
        assert set(fn.keys()) == {"name", "params", "instrs"}
        assert fn["name"] == fn_name
        assert isinstance(fn["params"], list)
        assert fn["instrs"], "function must have at least one instruction"

        ids = []
        labels_defined = set()
        labels_referenced = set()

        for instr in fn["instrs"]:
            assert set(instr.keys()) == INSTR_FIELDS, f"unexpected keys in {instr}"
            assert instr["op"] in VALID_OPS, f"unknown op {instr['op']!r}"
            assert isinstance(instr["id"], int)
            assert isinstance(instr["line"], int) and instr["line"] >= 1
            assert isinstance(instr["src"], str) and instr["src"]
            assert isinstance(instr["args"], list)
            ids.append(instr["id"])

            if instr["op"] == "label":
                assert instr["label"], "label op must set `label`"
                labels_defined.add(instr["label"])
            if instr["op"] in ("goto", "if_false", "if_true"):
                assert instr["target"], f"{instr['op']} must set `target`"
                labels_referenced.add(instr["target"])
            if instr["op"] == "binop":
                assert instr["operator"] in {
                    "+", "-", "*", "/", "%", "<", "<=", ">", ">=", "==", "!=", "&&", "||"
                }
                assert instr["arg1"] is not None and instr["arg2"] is not None
            if instr["op"] == "unop":
                assert instr["operator"] in {"-", "!"}
                assert instr["arg1"] is not None
            if instr["op"] == "call":
                assert instr["arg1"], "call must name the function in arg1"

        # ids unique within the function (per section 6: stable, never reused)
        assert len(ids) == len(set(ids)), f"duplicate instr ids in {fn_name}"
        # every referenced label must be defined somewhere in the function
        assert labels_referenced <= labels_defined, (
            f"{fn_name} references undefined label(s): "
            f"{labels_referenced - labels_defined}"
        )

        seen_ids_by_fn[fn_name] = ids


def test_manifest_lists_every_fixture(manifest):
    manifest_files = {entry["file"] for entry in manifest}
    disk_files = {p.name for p in _fixture_files()}
    assert manifest_files == disk_files
    for entry in manifest:
        assert entry["description"]
        assert entry["expected_passes"]
        assert entry["expected_outcome"]
