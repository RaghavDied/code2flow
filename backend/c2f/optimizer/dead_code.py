"""dead_code pass. Owner: Ishani. Signature: def run(fn: TacFunction) -> list[LogEntry]."""
from __future__ import annotations

from typing import List

from c2f.ir import TacFunction
from c2f.optimizer._support import render
from c2f.optimizer.dataflow import LiveVariables, def_use
from c2f.optimizer.manager import LogEntry

PASS_NAME = "dead_code_elimination"

# Only remove instructions with no possible side effect beyond defining a
# variable. `call` is never removed here even if its result is unused --
# the called function (printf, scanf, or a user function) may have effects
# this pass can't see.
_SAFE_TO_REMOVE_OPS = {"assign", "binop", "unop", "array_load"}


def run(fn: TacFunction) -> List[LogEntry]:
    log: List[LogEntry] = []
    live = LiveVariables(fn).solve()

    keep = []
    for instr in fn.instrs:
        if instr.op in _SAFE_TO_REMOVE_OPS:
            defs, _ = def_use(instr)
            if len(defs) == 1:
                (var,) = tuple(defs)
                if live.is_dead_assignment(instr, var):
                    before = render(instr)
                    log.append(LogEntry(PASS_NAME, fn.name, instr.line, instr.id, "removed", before, ""))
                    continue
        keep.append(instr)

    fn.instrs = keep
    return log
