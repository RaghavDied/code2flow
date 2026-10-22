"""const_prop pass. Owner: Ishani. Signature: def run(fn: TacFunction) -> list[LogEntry]."""
from __future__ import annotations

from typing import List

from c2f.ir import TacFunction, is_literal
from c2f.optimizer._support import render
from c2f.optimizer.dataflow import ReachingDefinitions
from c2f.optimizer.manager import LogEntry

PASS_NAME = "constant_propagation"

# Which operand fields are genuine *uses* for each op (per CONTRACTS.md section 6).
# `call`'s arg1 is a function name, never a variable, so it's handled separately
# via `args`; array ops are left alone (no fixtures exercise them, and
# propagating into an index needs more care than a flat text substitution).
_USE_FIELDS = {
    "assign": ["arg1"],
    "binop": ["arg1", "arg2"],
    "unop": ["arg1"],
    "if_false": ["arg1"],
    "if_true": ["arg1"],
    "return": ["arg1"],
}


def run(fn: TacFunction) -> List[LogEntry]:
    log: List[LogEntry] = []
    rd = ReachingDefinitions(fn).solve()
    by_id = {i.id: i for i in fn.instrs}

    def try_propagate(instr, operand: str) -> str | None:
        """Return the literal text to substitute for `operand`, or None."""
        if operand is None or is_literal(operand):
            return None
        reaching = rd.reaching_at_use(instr, operand)
        if len(reaching) != 1:
            return None
        def_instr = by_id[next(iter(reaching))]
        if def_instr.op == "assign" and is_literal(def_instr.arg1):
            return def_instr.arg1
        return None

    for instr in fn.instrs:
        for field_name in _USE_FIELDS.get(instr.op, []):
            operand = getattr(instr, field_name)
            literal_text = try_propagate(instr, operand)
            if literal_text is None:
                continue
            before = render(instr)
            setattr(instr, field_name, literal_text)
            after = render(instr)
            log.append(LogEntry(PASS_NAME, fn.name, instr.line, instr.id, "replaced", before, after))

        if instr.op == "call":
            for idx, a in enumerate(instr.args):
                literal_text = try_propagate(instr, a)
                if literal_text is None:
                    continue
                before = render(instr)
                instr.args[idx] = literal_text
                after = render(instr)
                log.append(LogEntry(PASS_NAME, fn.name, instr.line, instr.id, "replaced", before, after))

    return log
