"""
c2f/optimizer/dataflow.py  (Ishani)

Dataflow framework used by the optimisation passes:
  - reaching definitions   -> constant_propagation, copy_propagation
  - live-variable analysis -> dead_code_elimination

Design note: the project doc (section 5/7) frames these as running over
"basic blocks". This module instead runs the worklist at *instruction*
granularity, using each TacFunction's own labels/goto/if_true/if_false to
build successor/predecessor edges directly. That's a strict refinement of
block-level dataflow (same fixed point, finer-grained results) and keeps
c2f.optimizer decoupled from c2f.cfg (Raghav's basic-block partitioning is
about flowchart rendering; the optimiser only needs def/use reachability).
If this turns out to be more expensive than block-level for large programs
we can switch to blocks later without changing any pass's public behaviour.

Public API:
  def_use(instr)                          -> (defs: set[str], uses: set[str])
  successors(fn) / predecessors(fn)        -> dict[int, list[int]]  (keyed by TacInstr.id)
  ReachingDefinitions(fn).solve()          -> ReachingDefsResult
  LiveVariables(fn).solve()                -> LivenessResult
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    from c2f.ir import TacFunction, TacInstr, is_literal  # type: ignore
except ImportError:  # pragma: no cover - c2f.ir not landed yet, see _tac_contract_stub
    from c2f.optimizer._tac_contract_stub import TacFunction, TacInstr, is_literal

# A "definition" for reaching-definitions purposes: which instr id assigned which variable.
Definition = tuple[str, int]  # (var_name, defining_instr_id)

JUMP_OPS = {"goto", "if_false", "if_true"}
EXIT_OPS = {"return"}


def _operand_var(operand: str | None) -> str | None:
    """Return `operand` if it names a variable/temporary, else None (literal or absent)."""
    if operand is None or is_literal(operand):
        return None
    return operand


def def_use(instr: TacInstr) -> tuple[set[str], set[str]]:
    """
    Return (defs, uses): the set of variable/temporary names an instruction
    defines and the set it reads, per the op semantics in CONTRACTS.md section 6.
    `array_store` is treated conservatively: it USES the array name, the index
    and the stored value, and defines nothing named (element-level defs aren't
    tracked at this granularity).
    """
    defs: set[str] = set()
    uses: set[str] = set()
    op = instr.op

    if op == "assign":
        if instr.result:
            defs.add(instr.result)
        v = _operand_var(instr.arg1)
        if v:
            uses.add(v)
    elif op == "binop":
        if instr.result:
            defs.add(instr.result)
        for v in (_operand_var(instr.arg1), _operand_var(instr.arg2)):
            if v:
                uses.add(v)
    elif op == "unop":
        if instr.result:
            defs.add(instr.result)
        v = _operand_var(instr.arg1)
        if v:
            uses.add(v)
    elif op in ("if_false", "if_true"):
        v = _operand_var(instr.arg1)
        if v:
            uses.add(v)
    elif op == "call":
        if instr.result:
            defs.add(instr.result)
        for a in instr.args:
            v = _operand_var(a)
            if v:
                uses.add(v)
    elif op == "return":
        v = _operand_var(instr.arg1)
        if v:
            uses.add(v)
    elif op == "array_load":
        if instr.result:
            defs.add(instr.result)
        for v in (_operand_var(instr.arg1), _operand_var(instr.arg2)):
            if v:
                uses.add(v)
    elif op == "array_store":
        for v in (_operand_var(instr.arg1), _operand_var(instr.arg2), _operand_var(instr.result)):
            if v:
                uses.add(v)
    # "label" / "goto": no defs, no uses.

    return defs, uses


def _label_index(fn: TacFunction) -> dict[str, int]:
    idx = {}
    for i, instr in enumerate(fn.instrs):
        if instr.op == "label":
            idx[instr.label] = i
    return idx


def successors(fn: TacFunction) -> dict[int, list[int]]:
    """instr.id -> list of successor instr.id, per this function's own control flow."""
    labels = _label_index(fn)
    n = len(fn.instrs)
    succ: dict[int, list[int]] = {}
    for i, instr in enumerate(fn.instrs):
        outs: list[int] = []
        if instr.op == "goto":
            outs.append(fn.instrs[labels[instr.target]].id)
        elif instr.op in ("if_false", "if_true"):
            if i + 1 < n:
                outs.append(fn.instrs[i + 1].id)
            outs.append(fn.instrs[labels[instr.target]].id)
        elif instr.op in EXIT_OPS:
            pass  # no successors, function exit
        else:
            if i + 1 < n:
                outs.append(fn.instrs[i + 1].id)
        succ[instr.id] = outs
    return succ


def predecessors(fn: TacFunction) -> dict[int, list[int]]:
    succ = successors(fn)
    pred: dict[int, list[int]] = {instr.id: [] for instr in fn.instrs}
    for src_id, targets in succ.items():
        for t in targets:
            pred[t].append(src_id)
    return pred


@dataclass
class ReachingDefsResult:
    """IN/OUT sets of `Definition`s, keyed by TacInstr.id."""
    in_sets: dict[int, frozenset[Definition]]
    out_sets: dict[int, frozenset[Definition]]

    def reaching_at_use(self, instr: TacInstr, var: str) -> frozenset[int]:
        """Instr ids of the definitions of `var` that reach the *start* of `instr`."""
        return frozenset(
            def_id for (def_var, def_id) in self.in_sets[instr.id] if def_var == var
        )


class ReachingDefinitions:
    """Forward, may-reach dataflow analysis: IN[i] = U OUT[p] for p in preds(i);
    OUT[i] = GEN(i) | (IN[i] - KILL(i))."""

    def __init__(self, fn: TacFunction):
        self.fn = fn
        self.succ = successors(fn)
        self.pred = predecessors(fn)
        self._by_id = {instr.id: instr for instr in fn.instrs}

    def solve(self) -> ReachingDefsResult:
        fn = self.fn
        # all_defs_of[var] = every instr id that defines var, anywhere in the function
        all_defs_of: dict[str, set[int]] = {}
        gen: dict[int, set[Definition]] = {}
        for instr in fn.instrs:
            defs, _ = def_use(instr)
            gen[instr.id] = {(v, instr.id) for v in defs}
            for v in defs:
                all_defs_of.setdefault(v, set()).add(instr.id)

        in_sets: dict[int, set[Definition]] = {instr.id: set() for instr in fn.instrs}
        out_sets: dict[int, set[Definition]] = {instr.id: set() for instr in fn.instrs}

        worklist = list(fn.instrs)
        while worklist:
            instr = worklist.pop(0)
            new_in: set[Definition] = set()
            for p in self.pred[instr.id]:
                new_in |= out_sets[p]

            defs, _ = def_use(instr)
            kill = {
                (v, other_id)
                for v in defs
                for other_id in all_defs_of.get(v, ())
                if other_id != instr.id
            }
            new_out = gen[instr.id] | (new_in - kill)

            if new_in != in_sets[instr.id] or new_out != out_sets[instr.id]:
                in_sets[instr.id] = new_in
                out_sets[instr.id] = new_out
                for s in self.succ[instr.id]:
                    succ_instr = self._by_id[s]
                    if succ_instr not in worklist:
                        worklist.append(succ_instr)

        return ReachingDefsResult(
            in_sets={k: frozenset(v) for k, v in in_sets.items()},
            out_sets={k: frozenset(v) for k, v in out_sets.items()},
        )


@dataclass
class LivenessResult:
    """IN/OUT sets of live variable names, keyed by TacInstr.id."""
    in_sets: dict[int, frozenset[str]]
    out_sets: dict[int, frozenset[str]]

    def is_dead_assignment(self, instr: TacInstr, defined_var: str) -> bool:
        """True if `defined_var`, defined by `instr`, is not live immediately after it."""
        return defined_var not in self.out_sets[instr.id]


class LiveVariables:
    """Backward, may-be-used-later dataflow analysis: OUT[i] = U IN[s] for s in succ(i);
    IN[i] = USE(i) | (OUT[i] - DEF(i))."""

    def __init__(self, fn: TacFunction):
        self.fn = fn
        self.succ = successors(fn)
        self.pred = predecessors(fn)
        self._by_id = {instr.id: instr for instr in fn.instrs}

    def solve(self) -> LivenessResult:
        fn = self.fn
        in_sets: dict[int, set[str]] = {instr.id: set() for instr in fn.instrs}
        out_sets: dict[int, set[str]] = {instr.id: set() for instr in fn.instrs}

        worklist = list(fn.instrs)
        while worklist:
            instr = worklist.pop(0)
            new_out: set[str] = set()
            for s in self.succ[instr.id]:
                new_out |= in_sets[s]

            defs, uses = def_use(instr)
            new_in = uses | (new_out - defs)

            if new_in != in_sets[instr.id] or new_out != out_sets[instr.id]:
                in_sets[instr.id] = new_in
                out_sets[instr.id] = new_out
                for p in self.pred[instr.id]:
                    pred_instr = self._by_id[p]
                    if pred_instr not in worklist:
                        worklist.append(pred_instr)

        return LivenessResult(
            in_sets={k: frozenset(v) for k, v in in_sets.items()},
            out_sets={k: frozenset(v) for k, v in out_sets.items()},
        )
