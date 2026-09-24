"""CFG data model + builder (CONTRACTS.md section 7). Owner: Raghav (defined with Sneh)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from c2f.ir import TacFunction

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
            {"id": n.id, "type": n.type, "label": n.label, "lines": list(n.lines),
             "instr_ids": list(n.instr_ids), "is_loop_header": n.is_loop_header}
            for n in cfg.nodes
        ],
        "edges": [
            {"source": e.source, "target": e.target, "label": e.label,
             "is_back_edge": e.is_back_edge}
            for e in cfg.edges
        ],
    }


def cfg_from_dict(d: dict) -> Cfg:
    """Inverse of cfg_to_dict (used by tests and tools)."""
    return Cfg(
        function=d["function"],
        nodes=[CfgNode(n["id"], n["type"], n["label"], list(n["lines"]),
                       list(n["instr_ids"]), n["is_loop_header"]) for n in d["nodes"]],
        edges=[CfgEdge(e["source"], e["target"], e["label"], e["is_back_edge"]) for e in d["edges"]],
    )


def build_cfg(fn: TacFunction) -> Cfg:
    """Split TAC into basic blocks and connect them. TODO (Week 2-3)."""
    raise NotImplementedError("build_cfg is not implemented yet (Raghav, Week 2-3)")
