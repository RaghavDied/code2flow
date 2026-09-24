"""API envelope / contract tests against the mock pipeline. Owner: Raghav."""
import filecmp
from pathlib import Path

import pytest

from c2f.common import Diagnostic, make_error, make_warning
from c2f.optimizer import LogEntry

OK_CODE = "int main() { return 0; }"
ENVELOPE_KEYS = {"ok", "errors", "warnings", "data"}
DIAG_KEYS = {"phase", "severity", "message", "line", "col"}


def post(client, path, code=OK_CODE, language="c"):
    r = client.post(path, json={"language": language, "code": code})
    assert r.status_code == 200
    return r.json()


@pytest.mark.parametrize("path", ["/api/tokens", "/api/ast", "/api/generate", "/api/optimize"])
def test_envelope_shape_and_ok_invariant(client, path):
    body = post(client, path)
    assert set(body) == ENVELOPE_KEYS
    assert body["ok"] is True and body["errors"] == [] and body["data"] is not None


@pytest.mark.parametrize("path", ["/api/tokens", "/api/ast", "/api/generate", "/api/optimize"])
def test_compile_error_is_http_200_with_null_data(client, path):
    body = post(client, path, code="int main( { return 0; }")
    assert body["ok"] is False and body["data"] is None and body["errors"]
    for d in body["errors"]:
        assert set(d) == DIAG_KEYS and d["severity"] == "error" and d["line"] >= 1 and d["col"] >= 1


def test_empty_source_is_an_error(client):
    body = post(client, "/api/generate", code="   \n")
    assert body["ok"] is False and body["errors"][0]["phase"] == "parser"


def test_unsupported_language_is_an_error(client):
    body = post(client, "/api/generate", language="python")
    assert body["ok"] is False and "Unsupported language" in body["errors"][0]["message"]


def test_data_keys_per_endpoint(client):
    assert set(post(client, "/api/tokens")["data"]) == {"tokens"}
    assert set(post(client, "/api/ast")["data"]) == {"ast"}
    gen = post(client, "/api/generate")["data"]
    assert set(gen) == {"functions", "ast", "tac", "cfg", "metrics"}
    assert set(gen["tac"]) == set(gen["cfg"]) == set(gen["metrics"]) == set(gen["functions"])
    opt = post(client, "/api/optimize")["data"]
    assert set(opt) == {"functions", "original", "optimized", "log", "optimized_c", "warnings_dead_code"}
    for side in ("original", "optimized"):
        assert set(opt[side]) == {"tac", "cfg", "metrics"}


def test_optimize_log_matches_logentry_contract(client):
    opt = post(client, "/api/optimize")["data"]
    passes = {"constant_folding", "constant_propagation", "algebraic_simplification",
              "dead_code_elimination", "unreachable_code_removal", "branch_simplification",
              "strength_reduction", "copy_propagation", "common_subexpression_elimination",
              "loop_invariant_code_motion"}
    for entry in opt["log"]:
        le = LogEntry(**entry)
        assert le.pass_name in passes
        assert le.action in ("replaced", "removed", "added", "moved")
    for w in opt["warnings_dead_code"]:
        Diagnostic.from_dict(w)


def test_cors_allows_the_vite_dev_server(client):
    r = client.options("/api/generate", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_frontend_mocks_are_copies_of_backend_fixtures(fixtures_dir):
    mocks = Path(__file__).resolve().parents[2] / "frontend" / "src" / "mocks"
    for f in sorted(fixtures_dir.glob("*.json")):
        assert (mocks / f.name).exists(), f"missing mock copy of {f.name}"
        assert filecmp.cmp(f, mocks / f.name, shallow=False), f"{f.name} differs between fixtures and mocks"


def test_diagnostic_validation_and_roundtrip():
    d = make_error("parser", "Expected ')'", 1, 11)
    assert Diagnostic.from_dict(d.to_dict()) == d
    assert make_warning("semantic", "unused", 4, 9).severity == "warning"
    with pytest.raises(ValueError):
        Diagnostic("linker", "error", "x", 1, 1)
    with pytest.raises(ValueError):
        Diagnostic("parser", "fatal", "x", 1, 1)
    with pytest.raises(ValueError):
        Diagnostic("parser", "error", "x", 0, 1)
