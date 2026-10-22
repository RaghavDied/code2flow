"""Dominator analysis for Control Flow Graphs.

Owner: Raghav (doc section 4, CONTRACTS.md section 7).
Computes dominator sets and immediate dominators using standard fixed-point iteration.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Set

if TYPE_CHECKING:
    from .cfg_builder import Cfg


def compute_dominators(cfg: Cfg) -> Dict[str, Set[str]]:
    """Compute dominator sets for all nodes in the CFG.

    A node d dominates n if every path from the entry node (B0) to n goes through d.
    Dom(B0) = {B0}
    Dom(n) = {n} U (intersection of Dom(p) for all predecessors p of n)
    """
    if not cfg.nodes:
        return {}

    all_node_ids = {n.id for n in cfg.nodes}
    entry_id = "B0" if "B0" in all_node_ids else cfg.nodes[0].id

    # Predecessors map
    preds: Dict[str, Set[str]] = {n.id: set() for n in cfg.nodes}
    for e in cfg.edges:
        if e.target in preds:
            preds[e.target].add(e.source)

    # Initialize
    dom: Dict[str, Set[str]] = {n.id: set(all_node_ids) for n in cfg.nodes}
    dom[entry_id] = {entry_id}

    changed = True
    while changed:
        changed = False
        for node in cfg.nodes:
            nid = node.id
            if nid == entry_id:
                continue

            node_preds = preds.get(nid, set())
            if not node_preds:
                new_dom = {nid}
            else:
                pred_doms = [dom[p] for p in node_preds if p in dom]
                if pred_doms:
                    common_dom = set.intersection(*pred_doms)
                else:
                    common_dom = set()
                new_dom = {nid} | common_dom

            if new_dom != dom[nid]:
                dom[nid] = new_dom
                changed = True

    return dom


def compute_immediate_dominators(cfg: Cfg) -> Dict[str, Optional[str]]:
    """Compute the immediate dominator (idom) for each node."""
    doms = compute_dominators(cfg)
    idoms: Dict[str, Optional[str]] = {}

    entry_id = "B0" if any(n.id == "B0" for n in cfg.nodes) else (cfg.nodes[0].id if cfg.nodes else "")

    for nid, d_set in doms.items():
        if nid == entry_id:
            idoms[nid] = None
            continue

        strict_doms = d_set - {nid}
        # idom is the unique d in strict_doms that is dominated by all other strict_doms
        idom = None
        for candidate in strict_doms:
            if all(other in doms[candidate] for other in strict_doms if other != candidate):
                idom = candidate
                break

        idoms[nid] = idom

    return idoms
