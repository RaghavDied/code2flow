"""Per-function CFG metrics (CONTRACTS.md section 8). Owner: Raghav."""
from __future__ import annotations

from c2f.cfg import Cfg


def compute_metrics(cfg: Cfg) -> dict:
    """Return {nodes, edges, decisions, loops, cyclomatic_complexity} for one CFG.

    loops = number of back edges. cyclomatic_complexity = edges - nodes + 2.
    """
    nodes = len(cfg.nodes)
    edges = len(cfg.edges)
    return {
        "nodes": nodes,
        "edges": edges,
        "decisions": sum(1 for n in cfg.nodes if n.type == "decision"),
        "loops": sum(1 for e in cfg.edges if e.is_back_edge),
        "cyclomatic_complexity": edges - nodes + 2,
    }
