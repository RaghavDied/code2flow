"""algebraic pass. Owner: Ishani. Signature: def run(fn: TacFunction) -> list[LogEntry]."""
from __future__ import annotations

from typing import List, Optional

from c2f.ir import TacFunction, is_literal
from c2f.optimizer._support import parse_literal, render
from c2f.optimizer.manager import LogEntry

PASS_NAME = "algebraic_simplification"


def _identity_replacement(op: str, arg1: str, arg2: str) -> Optional[str]:
    """Return the operand text that should replace the whole binop, or None."""
    a_lit = is_literal(arg1)
    b_lit = is_literal(arg2)
    a_val = parse_literal(arg1) if a_lit else None
    b_val = parse_literal(arg2) if b_lit else None

    if op == "*":
        if b_lit and b_val == 1:
            return arg1
        if a_lit and a_val == 1:
            return arg2
        if (a_lit and a_val == 0) or (b_lit and b_val == 0):
            return "0"
    elif op == "+":
        if b_lit and b_val == 0:
            return arg1
        if a_lit and a_val == 0:
            return arg2
    elif op == "-":
        if b_lit and b_val == 0:
            return arg1
    elif op == "/":
        if b_lit and b_val == 1:
            return arg1
    return None


def run(fn: TacFunction) -> List[LogEntry]:
    log: List[LogEntry] = []
    for instr in fn.instrs:
        if instr.op != "binop":
            continue
        replacement = _identity_replacement(instr.operator, instr.arg1, instr.arg2)
        if replacement is None:
            continue
        before = render(instr)
        instr.op = "assign"
        instr.arg1 = replacement
        instr.arg2 = None
        instr.operator = None
        after = render(instr)
        log.append(LogEntry(PASS_NAME, fn.name, instr.line, instr.id, "replaced", before, after))
    return log
