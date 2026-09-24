"""Three-address-code data model (CONTRACTS.md section 6).

Owner: Raghav (defined with Ishani). Instruction ids are stable: the optimiser never
renumbers instructions it keeps, and new instructions get max id + 1.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

OPS = (
    "assign", "binop", "unop", "label", "goto", "if_false", "if_true",
    "call", "return", "array_load", "array_store",
)
BINARY_OPERATORS = ("+", "-", "*", "/", "%", "<", "<=", ">", ">=", "==", "!=", "&&", "||")
UNARY_OPERATORS = ("-", "!")

_TEMP_RE = re.compile(r"^t[0-9]+$")
_INT_RE = re.compile(r"^-?[0-9]+$")
_FLOAT_RE = re.compile(r"^-?([0-9]+\.[0-9]*|\.[0-9]+)$")
_CHAR_RE = re.compile(r"^'(\\.|[^'\\])'$")
_STRING_RE = re.compile(r'^"(\\.|[^"\\])*"$')


def is_literal(operand: str) -> bool:
    """True if operand is a literal's source text ("5", "3.5", "'a'", '"hi"')."""
    return bool(
        _INT_RE.match(operand) or _FLOAT_RE.match(operand)
        or _CHAR_RE.match(operand) or _STRING_RE.match(operand)
    )


def is_temp(operand: str) -> bool:
    """True if operand is a compiler temporary (t1, t2, ...)."""
    return bool(_TEMP_RE.match(operand))


@dataclass
class TacInstr:
    """One TAC instruction. Field meaning per op is in CONTRACTS.md section 6."""

    id: int
    op: str
    result: Optional[str] = None
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    operator: Optional[str] = None      # only binop / unop
    target: Optional[str] = None        # only goto / if_false / if_true
    label: Optional[str] = None         # only op == "label"
    args: List[str] = field(default_factory=list)  # only call
    line: int = 1                       # source line, 1-based
    src: str = ""                       # source text for flowchart labels

    def __post_init__(self) -> None:
        # Malformed instructions are programmer bugs, so raising is allowed.
        if self.op not in OPS:
            raise ValueError(f"unknown TAC op {self.op!r}")
        if self.op == "binop" and self.operator not in BINARY_OPERATORS:
            raise ValueError(f"binop needs an operator in {BINARY_OPERATORS}, got {self.operator!r}")
        if self.op == "unop" and self.operator not in UNARY_OPERATORS:
            raise ValueError(f"unop needs an operator in {UNARY_OPERATORS}, got {self.operator!r}")
        if self.op == "label" and not self.label:
            raise ValueError("label instruction needs a label name")
        if self.op in ("goto", "if_false", "if_true") and not self.target:
            raise ValueError(f"{self.op} needs a target label")
        if self.op in ("if_false", "if_true") and self.arg1 is None:
            raise ValueError(f"{self.op} needs arg1 (the condition operand)")
        if self.op == "call" and not self.arg1:
            raise ValueError("call needs arg1 (the function name)")

    def to_dict(self) -> dict:
        """JSON dict with every contract field (null / [] when unused)."""
        return {
            "id": self.id, "op": self.op, "result": self.result,
            "arg1": self.arg1, "arg2": self.arg2, "operator": self.operator,
            "target": self.target, "label": self.label, "args": list(self.args),
            "line": self.line, "src": self.src,
        }

    @staticmethod
    def from_dict(d: dict) -> "TacInstr":
        """Inverse of to_dict."""
        return TacInstr(
            id=d["id"], op=d["op"], result=d.get("result"), arg1=d.get("arg1"),
            arg2=d.get("arg2"), operator=d.get("operator"), target=d.get("target"),
            label=d.get("label"), args=list(d.get("args") or []),
            line=d.get("line", 1), src=d.get("src", ""),
        )


@dataclass
class TacFunction:
    """TAC of one C function."""

    name: str
    params: List[str]
    instrs: List[TacInstr]

    def to_list(self) -> List[dict]:
        """The list of TacInstr JSON used under data.tac[<fn>] in the API."""
        return [i.to_dict() for i in self.instrs]


@dataclass
class TacProgram:
    """TAC of the whole program. Key = function name, in source order."""

    functions: Dict[str, TacFunction] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, List[dict]]:
        """{fn_name: [TacInstr JSON]} exactly as the API's data.tac."""
        return {name: fn.to_list() for name, fn in self.functions.items()}

    @staticmethod
    def from_dict(d: Dict[str, List[dict]]) -> "TacProgram":
        """Inverse of to_dict. The API JSON carries no params, so params is []."""
        return TacProgram({
            name: TacFunction(name, [], [TacInstr.from_dict(i) for i in instrs])
            for name, instrs in d.items()
        })

    def next_id(self) -> int:
        """Fresh instruction id: max existing id + 1 (1 if empty)."""
        ids = [i.id for fn in self.functions.values() for i in fn.instrs]
        return (max(ids) + 1) if ids else 1
