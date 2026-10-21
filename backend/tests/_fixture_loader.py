"""
backend/tests/_fixture_loader.py (Ishani)

Loads backend/tests/fixtures/tac/*.json into real c2f.ir TacProgram objects.

Not c2f.ir.TacProgram.from_dict(): that method assumes the API wire format
{fn_name: [instr dicts]} with no params field (params is always set to []).
Our fixtures intentionally carry each function's `params` (some optimiser
tests need parameters, e.g. a function that takes `n` or `y`), so this
loader reads the fuller {"functions": {fn_name: {name, params, instrs}}}
shape instead.
"""
import json

from c2f.ir import TacFunction, TacInstr, TacProgram


def load_tac_program(path: str) -> TacProgram:
    with open(path) as f:
        data = json.load(f)
    functions = {}
    for fn_name, fn in data["functions"].items():
        instrs = [TacInstr(**i) for i in fn["instrs"]]
        functions[fn_name] = TacFunction(name=fn["name"], params=fn["params"], instrs=instrs)
    return TacProgram(functions=functions)
