"""constant_fold pass. Owner: Ishani. Signature: def run(fn: TacFunction) -> list[LogEntry]."""
from __future__ import annotations

from typing import List

from c2f.ir import TacFunction, is_literal
from c2f.optimizer._support import apply_binop, apply_unop, format_literal, parse_literal, render
from c2f.optimizer.manager import LogEntry

PASS_NAME = "constant_folding"


def run(fn: TacFunction) -> List[LogEntry]:
    log: List[LogEntry] = []
    for instr in fn.instrs:
        if instr.op == "binop" and is_literal(instr.arg1) and is_literal(instr.arg2):
            before = render(instr)
            a = parse_literal(instr.arg1)
            b = parse_literal(instr.arg2)
            try:
                value = apply_binop(instr.operator, a, b)
            except ZeroDivisionError:
                continue  # leave div/mod-by-zero alone; not this pass's job to fail the build
            instr.op = "assign"
            instr.arg1 = format_literal(value)
            instr.arg2 = None
            instr.operator = None
            after = render(instr)
            log.append(LogEntry(PASS_NAME, fn.name, instr.line, instr.id, "replaced", before, after))

        elif instr.op == "unop" and is_literal(instr.arg1):
            before = render(instr)
            a = parse_literal(instr.arg1)
            value = apply_unop(instr.operator, a)
            instr.op = "assign"
            instr.arg1 = format_literal(value)
            instr.operator = None
            after = render(instr)
            log.append(LogEntry(PASS_NAME, fn.name, instr.line, instr.id, "replaced", before, after))

    return log
