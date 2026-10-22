"""Loop and back-edge detection for Control Flow Graphs.

Owner: Raghav (doc section 4, CONTRACTS.md section 7).
Identifies back edges (edges A -> B where B dominates A) and marks loop headers.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Set, Tuple

from .dominators import compute_dominators

if TYPE_CHECKING:
    from .cfg_builder import Cfg


def find_back_edges(cfg: Cfg) -> List[Tuple[str, str]]:
    """Return all back edges (source, target) where target dominates source."""
    doms = compute_dominators(cfg)
    back_edges: List[Tuple[str, str]] = []

    for e in cfg.edges:
        if e.target in doms.get(e.source, set()):
            back_edges.append((e.source, e.target))

    return back_edges


def mark_loops_and_back_edges(cfg: Cfg) -> None:
    """Detect and mark back edges and loop headers in-place on the CFG."""
    doms = compute_dominators(cfg)
    loop_header_ids: Set[str] = set()

    for edge in cfg.edges:
        if edge.target in doms.get(edge.source, set()):
            edge.is_back_edge = True
            loop_header_ids.add(edge.target)
        else:
            edge.is_back_edge = False

    for node in cfg.nodes:
        if node.id in loop_header_ids:
            node.is_loop_header = True
