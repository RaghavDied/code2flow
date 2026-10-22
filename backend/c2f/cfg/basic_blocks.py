"""Basic block partitioning for three-address code.

Owner: Raghav (doc section 4, CONTRACTS.md section 7).
Identifies leaders and partitions a list of TacInstr into basic blocks.
"""
from __future__ import annotations

from typing import List, Set

from c2f.ir import TacInstr


def partition_into_basic_blocks(instrs: List[TacInstr]) -> List[List[TacInstr]]:
    """Partition a sequence of TacInstr into basic blocks based on leader analysis.

    Leaders:
    1. The first instruction.
    2. Any target of a jump (label instruction).
    3. Any instruction immediately following a jump, branch, or return.
    """
    if not instrs:
        return []

    # Map label names to instruction indices
    label_indices: dict[str, int] = {}
    for idx, instr in enumerate(instrs):
        if instr.op == "label" and instr.label:
            label_indices[instr.label] = idx

    leader_indices: Set[int] = {0}

    for idx, instr in enumerate(instrs):
        if instr.op in ("goto", "if_false", "if_true"):
            if instr.target and instr.target in label_indices:
                leader_indices.add(label_indices[instr.target])
            if idx + 1 < len(instrs):
                leader_indices.add(idx + 1)
        elif instr.op == "return":
            if idx + 1 < len(instrs):
                leader_indices.add(idx + 1)
        elif instr.op == "label":
            leader_indices.add(idx)

    sorted_leaders = sorted(idx for idx in leader_indices if 0 <= idx < len(instrs))

    blocks: List[List[TacInstr]] = []
    for k in range(len(sorted_leaders)):
        start = sorted_leaders[k]
        end = sorted_leaders[k + 1] if k + 1 < len(sorted_leaders) else len(instrs)
        block = instrs[start:end]
        if block:
            blocks.append(block)

    return blocks
