"""unreachable pass. Owner: Ishani. Signature: def run(fn: TacFunction) -> list[LogEntry]."""
from __future__ import annotations

from typing import List

from c2f.ir import TacFunction
from c2f.optimizer._support import render
from c2f.optimizer.dataflow import successors
from c2f.optimizer.manager import LogEntry

PASS_NAME = "unreachable_code_removal"


def run(fn: TacFunction) -> List[LogEntry]:
    if not fn.instrs:
        return []

    succ = successors(fn)
    entry_id = fn.instrs[0].id

    reachable = set()
    stack = [entry_id]
    while stack:
        cur = stack.pop()
        if cur in reachable:
            continue
        reachable.add(cur)
        for nxt in succ.get(cur, []):
            if nxt not in reachable:
                stack.append(nxt)

    log: List[LogEntry] = []
    keep = []
    for instr in fn.instrs:
        if instr.id in reachable:
            keep.append(instr)
        else:
            before = render(instr)
            log.append(LogEntry(PASS_NAME, fn.name, instr.line, instr.id, "removed", before, ""))

    fn.instrs = keep
    return log
