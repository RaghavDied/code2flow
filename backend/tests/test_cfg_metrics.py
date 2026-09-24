"""Metrics must reproduce the numbers stored in the API fixtures. Owner: Raghav."""
import pytest

from c2f.cfg.cfg_builder import cfg_from_dict
from c2f.metrics import compute_metrics


def test_if_else_metrics(load_fixture):
    m = compute_metrics(cfg_from_dict(load_fixture("cfg_if_else")))
    assert m == {"nodes": 7, "edges": 7, "decisions": 1, "loops": 0, "cyclomatic_complexity": 2}


def test_while_metrics(load_fixture):
    m = compute_metrics(cfg_from_dict(load_fixture("cfg_while_loop")))
    assert m == {"nodes": 6, "edges": 6, "decisions": 1, "loops": 1, "cyclomatic_complexity": 2}


@pytest.mark.parametrize("path", [("generate_ok",), ("optimize_ok", "original"), ("optimize_ok", "optimized")])
def test_metrics_match_api_fixtures(load_fixture, path):
    node = load_fixture(path[0])["data"]
    for key in path[1:]:
        node = node[key]
    for fn, cfg in node["cfg"].items():
        assert compute_metrics(cfg_from_dict(cfg)) == node["metrics"][fn]


def test_optimisation_lowers_complexity(load_fixture):
    d = load_fixture("optimize_ok")["data"]
    assert d["optimized"]["metrics"]["main"]["cyclomatic_complexity"] < d["original"]["metrics"]["main"]["cyclomatic_complexity"]
