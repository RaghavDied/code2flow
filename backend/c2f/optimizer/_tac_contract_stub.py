"""
TEMPORARY development stub -- NOT part of the public contract.

CONTRACTS.md section 6 makes TacInstr / TacFunction / TacProgram / is_literal
the responsibility of `c2f.ir` (Raghav). This module mirrors that contract
exactly (field-for-field) purely so code in `c2f.optimizer` can be written
and unit-tested against the fixtures in backend/tests/fixtures/tac/ before
c2f/ir/tac.py exists.

Every module in this package that needs these types imports them like this:

    try:
        from c2f.ir import TacInstr, TacFunction, TacProgram, is_literal
    except ImportError:  # pragma: no cover - real ir package not landed yet
        from c2f.optimizer._tac_contract_stub import (
            TacInstr, TacFunction, TacProgram, is_literal,
        )

DELETE this file (and the fallback imports above) once `c2f/ir/__init__.py`
really exports these names -- at that point this stub would silently mask a
real contract mismatch if the two ever drift apart.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class TacInstr:
    id: int
    op: str
    result: str | None = None
    arg1: str | None = None
    arg2: str | None = None
    operator: str | None = None
    target: str | None = None
    label: str | None = None
    args: list[str] = field(default_factory=list)
    line: int = 0
    src: str = ""


@dataclass
class TacFunction:
    name: str
    params: list[str]
    instrs: list[TacInstr]


@dataclass
class TacProgram:
    functions: dict[str, TacFunction]


_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+$")


def is_literal(operand: str | None) -> bool:
    """True if `operand` is literal source text (int/float/char/string), not a name."""
    if operand is None:
        return False
    if operand.startswith('"') or operand.startswith("'"):
        return True
    if _INT_RE.match(operand) or _FLOAT_RE.match(operand):
        return True
    return False


def load_tac_program(path: str) -> TacProgram:
    """Load one of the hand-made fixtures in backend/tests/fixtures/tac/ into a TacProgram."""
    with open(path) as f:
        data = json.load(f)
    functions = {}
    for fn_name, fn in data["functions"].items():
        instrs = [TacInstr(**i) for i in fn["instrs"]]
        functions[fn_name] = TacFunction(name=fn["name"], params=fn["params"], instrs=instrs)
    return TacProgram(functions=functions)
