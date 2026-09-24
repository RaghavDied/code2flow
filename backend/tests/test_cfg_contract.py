"""CFG JSON contract checks on fixtures. Owner: Raghav."""
import copy

import pytest

from c2f.cfg import cfg_to_dict
from c2f.cfg.cfg_builder import cfg_from_dict


@pytest.mark.parametrize("name", ["cfg_if_else", "cfg_while_loop"])
def test_standalone_cfg_fixtures_are_valid(load_fixture, cfg_problems, name):
    assert cfg_problems(load_fixture(name)) == []


@pytest.mark.parametrize("name", ["cfg_if_else", "cfg_while_loop"])
def test_cfg_roundtrip(load_fixture, name):
    d = load_fixture(name)
    assert cfg_to_dict(cfg_from_dict(d)) == d


def test_all_api_cfgs_are_valid(load_fixture, cfg_problems):
    gen = load_fixture("generate_ok")["data"]
    opt = load_fixture("optimize_ok")["data"]
    for group in (gen["cfg"], opt["original"]["cfg"], opt["optimized"]["cfg"]):
        for cfg in group.values():
            assert cfg_problems(cfg) == []


def test_cfg_covers_every_tac_instruction_once(load_fixture):
    gen = load_fixture("generate_ok")["data"]
    opt = load_fixture("optimize_ok")["data"]
    for tac, cfg in ((gen["tac"], gen["cfg"]), (opt["original"]["tac"], opt["original"]["cfg"]),
                     (opt["optimized"]["tac"], opt["optimized"]["cfg"])):
        for fn, instrs in tac.items():
            in_tac = [i["id"] for i in instrs]
            in_cfg = [i for n in cfg[fn]["nodes"] for i in n["instr_ids"]]
            assert sorted(in_tac) == sorted(in_cfg)


def test_optimizer_ids_are_stable(load_fixture):
    """Every optimised instruction id already existed before (nothing renumbered)."""
    opt = load_fixture("optimize_ok")["data"]
    before = {i["id"] for i in opt["original"]["tac"]["main"]}
    after = {i["id"] for i in opt["optimized"]["tac"]["main"]}
    assert after <= before


def test_validator_catches_violations(load_fixture, cfg_problems):
    bad = load_fixture("cfg_if_else")
    b = copy.deepcopy(bad)
    b["edges"] = [e for e in b["edges"] if not (e["source"] == "B2" and e["label"] == "FALSE")]
    assert any("decision" in p for p in cfg_problems(b))

    b = copy.deepcopy(bad)
    b["nodes"][0]["label"] = "BEGIN"
    assert any("start" in p for p in cfg_problems(b))

    b = copy.deepcopy(bad)
    b["nodes"][3]["id"] = "B9"
    assert any("B0..B" in p for p in cfg_problems(b))

    w = load_fixture("cfg_while_loop")
    w["nodes"][2]["is_loop_header"] = False
    assert any("loop header" in p for p in cfg_problems(w))
