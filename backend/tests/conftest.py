"""Shared pytest fixtures. Owner: Raghav."""
import json
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))  # so `import c2f` and `import main` work from any cwd

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture(scope="session")
def load_fixture():
    """load_fixture("generate_ok") -> parsed JSON from backend/tests/fixtures."""
    def _load(name: str):
        return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    return _load


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def cfg_problems():
    """cfg_problems(cfg_dict) -> list of CONTRACTS.md section 7 violations (empty list = valid)."""
    def _check(cfg: dict) -> list:
        problems = []
        nodes, edges = cfg["nodes"], cfg["edges"]
        ids = [n["id"] for n in nodes]
        if ids != [f"B{i}" for i in range(len(nodes))]:
            problems.append(f"node ids must be B0..B{len(nodes) - 1} in order, got {ids}")
        if not nodes or nodes[0]["type"] != "start" or nodes[0]["label"] != "START":
            problems.append("B0 must be the start node with label START")
        ends = [n for n in nodes if n["type"] == "end"]
        if len(ends) != 1 or ends[0]["label"] != "END":
            problems.append("exactly one end node with label END is required")
        idset = set(ids)
        for e in edges:
            if e["source"] not in idset or e["target"] not in idset:
                problems.append(f"edge references unknown node: {e}")
        if problems:
            return problems
        by_node = {i: [e for e in edges if e["source"] == i] for i in ids}
        headers = {n["id"] for n in nodes if n["is_loop_header"]}
        for n in nodes:
            out = by_node[n["id"]]
            labels = sorted(e["label"] or "" for e in out)
            if n["type"] == "decision":
                if labels != ["FALSE", "TRUE"]:
                    problems.append(f"{n['id']}: decision needs exactly TRUE and FALSE edges, got {labels}")
                if not n["label"].endswith("?"):
                    problems.append(f"{n['id']}: decision label must end with '?'")
            else:
                if any(e["label"] for e in out):
                    problems.append(f"{n['id']}: only decision edges may be labelled")
                if n["type"] == "end" and out:
                    problems.append(f"{n['id']}: end node must have no outgoing edges")
                if n["type"] != "end" and not out:
                    problems.append(f"{n['id']}: non-end node has no outgoing edge")
        if any(e["target"] == "B0" for e in edges):
            problems.append("start node must have no incoming edges")
        for e in edges:
            if e["is_back_edge"] and e["target"] not in headers:
                problems.append(f"back edge {e['source']}->{e['target']} must target a loop header")
        seen, stack = set(), ["B0"]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(e["target"] for e in by_node[cur])
        if seen != idset:
            problems.append(f"unreachable nodes: {sorted(idset - seen)}")
        return problems
    return _check
