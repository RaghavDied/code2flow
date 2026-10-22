"""branch_simplify pass. Owner: Ishani. Signature: def run(fn: TacFunction) -> list[LogEntry]."""
from __future__ import annotations

from typing import List

from c2f.ir import TacFunction, is_literal
from c2f.optimizer._support import parse_literal, render
from c2f.optimizer.manager import LogEntry

PASS_NAME = "branch_simplification"


def run(fn: TacFunction) -> List[LogEntry]:
    log: List[LogEntry] = []
    keep = []

    for instr in fn.instrs:
        if instr.op in ("if_false", "if_true") and is_literal(instr.arg1):
            cond = bool(parse_literal(instr.arg1))
            # if_false jumps when the condition is FALSE; if_true jumps when TRUE.
            always_jumps = (not cond) if instr.op == "if_false" else cond

            before = render(instr)
            if always_jumps:
                instr.op = "goto"
                instr.arg1 = None
                after = render(instr)
                log.append(LogEntry(PASS_NAME, fn.name, instr.line, instr.id, "replaced", before, after))
                keep.append(instr)
            else:
                # Condition never holds for this branch direction -- the test
                # never fires, so the instruction is a pure no-op (execution
                # always falls through to the next instruction regardless).
                log.append(LogEntry(PASS_NAME, fn.name, instr.line, instr.id, "removed", before, ""))
            continue

        keep.append(instr)

    fn.instrs = keep
    return log
