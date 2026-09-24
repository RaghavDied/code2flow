"""Pass manager + optimiser API (CONTRACTS.md section 6). Owner: Ishani.
# SKELETON STUB created by Raghav. The owner replaces this file; keep the public names/signatures from CONTRACTS.md.
"""
from __future__ import annotations

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


def optimize(prog: TacProgram) -> OptimizeResult:
    """Must not mutate its input (deep-copy first)."""
    raise NotImplementedError("optimize is not implemented yet (Ishani)")
