"""Pass manager + optimiser API (CONTRACTS.md section 6). Owner: Ishani.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import List

from c2f.ir import TacProgram


@dataclass
class LogEntry:
    pass_name: str
    function: str
    line: int
    instr_id: int
    action: str      # "replaced" | "removed" | "added" | "moved"
    before: str
    after: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OptimizeResult:
    program: TacProgram
    log: List[LogEntry] = field(default_factory=list)


# Imported AFTER LogEntry/OptimizeResult are defined (each pass module does
# `from c2f.optimizer.manager import LogEntry`, so those names must already
# exist on this partially-initialised module by the time those imports run).
from c2f.optimizer import (  # noqa: E402
    algebraic,
    branch_simplify,
    const_prop,
    constant_fold,
    dead_code,
    unreachable,
)

# CONTRACTS.md section 3: core passes, in this fixed order.
CORE_PASSES = [constant_fold, algebraic, const_prop, dead_code, branch_simplify, unreachable]

_MAX_ROUNDS = 50  # safety cap against an accidental non-terminating pass


def optimize(prog: TacProgram) -> OptimizeResult:
    """Must not mutate its input (deep-copy first)."""
    new_prog = copy.deepcopy(prog)
    all_log: List[LogEntry] = []

    for fn in new_prog.functions.values():
        rounds = 0
        changed = True
        while changed and rounds < _MAX_ROUNDS:
            changed = False
            rounds += 1
            for pass_module in CORE_PASSES:
                entries = pass_module.run(fn)
                if entries:
                    changed = True
                    all_log.extend(entries)

    return OptimizeResult(program=new_prog, log=all_log)
