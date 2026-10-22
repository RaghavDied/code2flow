"""CFG data model and builder (CONTRACTS.md section 7).

Owner: Raghav (defined with Sneh).
Partitions three-address code into basic blocks, computes control flow edges,
detects back-edges and loop headers, and builds the full Cfg structure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from c2f.ir import TacFunction, TacInstr

from .basic_blocks import partition_into_basic_blocks
from .loops import mark_loops_and_back_edges

NODE_TYPES = ("start", "end", "process", "decision", "io")
EDGE_LABELS = (None, "TRUE", "FALSE")


@dataclass
class CfgNode:
    """One basic block / flowchart box."""

    id: str                      # "B0", "B1", ... creation order, per function
    type: str                    # one of NODE_TYPES
    label: str                   # text in the box; statements joined by "\n"; decisions end with "?"
    lines: List[int] = field(default_factory=list)      # source lines covered
    instr_ids: List[int] = field(default_factory=list)  # TacInstr ids inside this block
    is_loop_header: bool = False

    def __post_init__(self) -> None:
        if self.type not in NODE_TYPES:
            raise ValueError(f"CfgNode.type must be one of {NODE_TYPES}, got {self.type!r}")


@dataclass
class CfgEdge:
    """Directed edge between two nodes."""

    source: str
    target: str
    label: Optional[str] = None  # None | "TRUE" | "FALSE"
    is_back_edge: bool = False

    def __post_init__(self) -> None:
        if self.label not in EDGE_LABELS:
            raise ValueError(f"CfgEdge.label must be one of {EDGE_LABELS}, got {self.label!r}")


@dataclass
class Cfg:
    """Control flow graph of one function."""

    function: str
    nodes: List[CfgNode] = field(default_factory=list)
    edges: List[CfgEdge] = field(default_factory=list)

    def node(self, node_id: str) -> CfgNode:
        """Node by id (KeyError if missing)."""
        for n in self.nodes:
            if n.id == node_id:
                return n
        raise KeyError(node_id)

    def out_edges(self, node_id: str) -> List[CfgEdge]:
        """Edges leaving node_id."""
        return [e for e in self.edges if e.source == node_id]


def cfg_to_dict(cfg: Cfg) -> dict:
    """JSON shape from CONTRACTS.md section 7 for one function."""
    return {
        "function": cfg.function,
        "nodes": [
            {
                "id": n.id,
                "type": n.type,
                "label": n.label,
                "lines": list(n.lines),
                "instr_ids": list(n.instr_ids),
                "is_loop_header": n.is_loop_header,
            }
            for n in cfg.nodes
        ],
        "edges": [
            {
                "source": e.source,
                "target": e.target,
                "label": e.label,
                "is_back_edge": e.is_back_edge,
            }
            for e in cfg.edges
        ],
    }


def cfg_from_dict(d: dict) -> Cfg:
    """Inverse of cfg_to_dict (used by tests and tools)."""
    return Cfg(
        function=d["function"],
        nodes=[
            CfgNode(
                n["id"],
                n["type"],
                n["label"],
                list(n["lines"]),
                list(n["instr_ids"]),
                n["is_loop_header"],
            )
            for n in d["nodes"]
        ],
        edges=[
            CfgEdge(e["source"], e["target"], e["label"], e["is_back_edge"])
            for e in d["edges"]
        ],
    )


def _is_io_instruction(instr: TacInstr) -> bool:
    """True if instruction is printf/scanf call."""
    return instr.op == "call" and instr.arg1 in ("printf", "scanf")


def _determine_node_type(instrs: List[TacInstr]) -> str:
    """Determine whether block is 'decision', 'io', or 'process'."""
    if not instrs:
        return "process"

    last = instrs[-1]
    if last.op in ("if_false", "if_true"):
        return "decision"

    # Only executable instructions (ignore labels and unconditional jumps)
    work = [i for i in instrs if i.op not in ("label", "goto")]
    if work and all(_is_io_instruction(i) for i in work):
        return "io"

    return "process"


def _format_label(instrs: List[TacInstr], node_type: str) -> str:
    """Format box text. Decisions end with '?', statements joined by '\\n'."""
    if not instrs:
        return ""

    if node_type == "decision":
        last = instrs[-1]
        # Use src of condition
        cond_text = last.src.strip()
        if cond_text.endswith(";"):
            cond_text = cond_text[:-1].strip()
        if not cond_text.endswith("?"):
            cond_text = f"{cond_text}?"

        # Preceding statements in the same block if any
        preceding = [
            i.src.strip() for i in instrs[:-1]
            if i.op not in ("label", "goto") and i.src.strip()
        ]
        # Deduplicate consecutive identical statements if needed
        lines = []
        for p in preceding:
            p_clean = p.rstrip(";")
            if p_clean and (not lines or lines[-1] != p_clean):
                lines.append(p_clean)

        if lines:
            return "\n".join(lines) + "\n" + cond_text
        return cond_text

    # Process or IO: collect statement source texts, omitting labels and jumps
    stmt_lines: List[str] = []
    for i in instrs:
        if i.op in ("label", "goto"):
            continue
        s = i.src.strip()
        # Remove trailing semicolon for clean flowchart presentation
        if s.endswith(";"):
            s = s[:-1].strip()
        if s and (not stmt_lines or stmt_lines[-1] != s):
            stmt_lines.append(s)

    if not stmt_lines:
        # Fallback if block only had jumps/labels
        return instrs[0].src.strip() if instrs else "process"

    return "\n".join(stmt_lines)


def build_cfg(fn: TacFunction) -> Cfg:
    """Build a Control Flow Graph from a three-address code function."""
    raw_blocks = partition_into_basic_blocks(fn.instrs)

    # Empty function case
    if not raw_blocks:
        b0 = CfgNode(id="B0", type="start", label="START")
        b1 = CfgNode(id="B1", type="end", label="END")
        e0 = CfgEdge(source="B0", target="B1", label=None)
        return Cfg(function=fn.name, nodes=[b0, b1], edges=[e0])

    # Filter out blocks that contain ONLY label instructions that immediately lead to another block,
    # or keep them as standard blocks. Keeping all blocks ensures 1:1 mapping.
    nodes: List[CfgNode] = []
    edges: List[CfgEdge] = []

    # Map label names to the block index they start in
    label_to_block_idx: Dict[str, int] = {}
    for idx, blk in enumerate(raw_blocks):
        for instr in blk:
            if instr.op == "label" and instr.label:
                label_to_block_idx[instr.label] = idx

    # START node is always B0
    b0 = CfgNode(id="B0", type="start", label="START", lines=[], instr_ids=[])
    nodes.append(b0)

    # Create CfgNodes for all basic blocks
    block_nodes: List[CfgNode] = []
    for idx, blk in enumerate(raw_blocks):
        node_id = f"B{idx + 1}"
        node_type = _determine_node_type(blk)
        node_label = _format_label(blk, node_type)
        covered_lines = sorted(set(i.line for i in blk if i.line >= 1))
        instr_ids = [i.id for i in blk]

        node = CfgNode(
            id=node_id,
            type=node_type,
            label=node_label,
            lines=covered_lines,
            instr_ids=instr_ids,
        )
        nodes.append(node)
        block_nodes.append(node)

    # END node
    end_id = f"B{len(raw_blocks) + 1}"
    end_node = CfgNode(id=end_id, type="end", label="END", lines=[], instr_ids=[])
    nodes.append(end_node)

    # Edge from START to first basic block
    edges.append(CfgEdge(source="B0", target=block_nodes[0].id, label=None))

    # Connect basic blocks
    for idx, (blk, node) in enumerate(zip(raw_blocks, block_nodes)):
        last = blk[-1] if blk else None
        if last is None:
            continue

        if last.op == "return":
            edges.append(CfgEdge(source=node.id, target=end_node.id, label=None))

        elif last.op in ("if_false", "if_true"):
            target_idx = label_to_block_idx.get(last.target or "")
            jump_target_id = block_nodes[target_idx].id if target_idx is not None else end_node.id
            fall_through_id = block_nodes[idx + 1].id if idx + 1 < len(block_nodes) else end_node.id

            if last.op == "if_false":
                # CONTRACTS.md Section 7: "if_false: fall-through is TRUE, jump target is FALSE."
                edges.append(CfgEdge(source=node.id, target=fall_through_id, label="TRUE"))
                edges.append(CfgEdge(source=node.id, target=jump_target_id, label="FALSE"))
            else:
                # "if_true: the reverse." (jump target is TRUE, fall-through is FALSE)
                edges.append(CfgEdge(source=node.id, target=jump_target_id, label="TRUE"))
                edges.append(CfgEdge(source=node.id, target=fall_through_id, label="FALSE"))

        elif last.op == "goto":
            target_idx = label_to_block_idx.get(last.target or "")
            target_id = block_nodes[target_idx].id if target_idx is not None else end_node.id
            edges.append(CfgEdge(source=node.id, target=target_id, label=None))

        else:
            # Fall-through to next block or END
            target_id = block_nodes[idx + 1].id if idx + 1 < len(block_nodes) else end_node.id
            edges.append(CfgEdge(source=node.id, target=target_id, label=None))

    cfg = Cfg(function=fn.name, nodes=nodes, edges=edges)

    # Compute dominators and mark back edges + loop headers
    mark_loops_and_back_edges(cfg)

    return cfg
