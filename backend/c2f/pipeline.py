"""Pipeline wiring (CONTRACTS.md section 8).

Owner: Raghav.
Wires lexer, parser, semantic analyzer, TAC generator, CFG builder, metrics,
and optimizer into unified pipeline endpoints. When USE_MOCKS is True (default
while Kushan completes the parser), it serves validated mock envelopes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from c2f.common import Diagnostic, make_error

USE_MOCKS = False
_FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def make_envelope(
    errors: Optional[List[Diagnostic]] = None,
    warnings: Optional[List[Diagnostic]] = None,
    data: Optional[dict] = None,
) -> dict:
    """Build the one response envelope. ok is False iff errors is non-empty (then data is None)."""
    errors = errors or []
    return {
        "ok": not errors,
        "errors": [e.to_dict() for e in errors],
        "warnings": [w.to_dict() for w in (warnings or [])],
        "data": None if errors else data,
    }


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def _mock_gate(source: str) -> Optional[dict]:
    """Mock-mode input checks so the UI can exercise the error path.

    Empty source, or unbalanced ( ) / { }, returns an error envelope.
    """
    if not source.strip():
        return make_envelope([make_error("parser", "Source code is empty", 1, 1)])
    if source.count("(") != source.count(")") or source.count("{") != source.count("}"):
        return _load("generate_error")
    return None


def run_tokens(source: str) -> dict:
    """POST /api/tokens."""
    if USE_MOCKS:
        return _mock_gate(source) or _load("tokens_ok")

    gate = _mock_gate(source)
    if gate:
        return gate

    from c2f.lexer import tokenize

    res = tokenize(source)
    if res.errors:
        return make_envelope(errors=res.errors)
    return make_envelope(
        data={"tokens": [{"type": t.type.value if hasattr(t.type, "value") else str(t.type),
                          "lexeme": t.lexeme, "line": t.line, "col": t.col} for t in res.tokens]}
    )


def run_ast(source: str) -> dict:
    """POST /api/ast."""
    if USE_MOCKS:
        return _mock_gate(source) or _load("ast_ok")

    gate = _mock_gate(source)
    if gate:
        return gate

    from c2f.lexer import tokenize
    from c2f.syntax import ast_to_dict, parse

    lex_res = tokenize(source)
    if lex_res.errors:
        return make_envelope(errors=lex_res.errors)

    parse_res = parse(lex_res.tokens)
    if parse_res.errors:
        return make_envelope(errors=parse_res.errors)
    if parse_res.ast is None:
        return make_envelope(errors=[make_error("parser", "Empty AST returned", 1, 1)])

    return make_envelope(data={"ast": ast_to_dict(parse_res.ast)})


def run_pipeline(source: str, optimize: bool = False) -> dict:
    """POST /api/generate (optimize=False) and POST /api/optimize (optimize=True)."""
    if USE_MOCKS:
        return _mock_gate(source) or _load("optimize_ok" if optimize else "generate_ok")

    gate = _mock_gate(source)
    if gate:
        return gate

    from c2f.cfg import build_cfg, cfg_to_dict
    from c2f.ir import generate_tac
    from c2f.lexer import tokenize
    from c2f.metrics import compute_metrics
    from c2f.semantic import analyze
    from c2f.syntax import ast_to_dict, parse

    lex_res = tokenize(source)
    if lex_res.errors:
        return make_envelope(errors=lex_res.errors)

    parse_res = parse(lex_res.tokens)
    if parse_res.errors:
        return make_envelope(errors=parse_res.errors)
    if parse_res.ast is None:
        return make_envelope(errors=[make_error("parser", "Empty AST produced", 1, 1)])

    sem_res = analyze(parse_res.ast)
    if sem_res.errors:
        return make_envelope(errors=sem_res.errors, warnings=sem_res.warnings)

    ast = sem_res.ast or parse_res.ast
    ast_dict = ast_to_dict(ast)

    tac_prog = generate_tac(ast)
    fn_names = list(tac_prog.functions.keys())

    tac_dict = tac_prog.to_dict()
    cfg_dict = {}
    metrics_dict = {}

    for fn_name, fn_tac in tac_prog.functions.items():
        fn_cfg = build_cfg(fn_tac)
        cfg_dict[fn_name] = cfg_to_dict(fn_cfg)
        metrics_dict[fn_name] = compute_metrics(fn_cfg)

    if not optimize:
        return make_envelope(
            warnings=sem_res.warnings,
            data={
                "functions": fn_names,
                "ast": ast_dict,
                "tac": tac_dict,
                "cfg": cfg_dict,
                "metrics": metrics_dict,
            },
        )

    # Optimization branch
    from c2f.optimizer import optimize as run_optimizer, tac_to_c

    opt_res = run_optimizer(tac_prog)
    opt_tac_dict = opt_res.program.to_dict()
    opt_cfg_dict = {}
    opt_metrics_dict = {}

    for fn_name, fn_tac in opt_res.program.functions.items():
        fn_cfg = build_cfg(fn_tac)
        opt_cfg_dict[fn_name] = cfg_to_dict(fn_cfg)
        opt_metrics_dict[fn_name] = compute_metrics(fn_cfg)

    log_entries = [
        {
            "pass_name": entry.pass_name,
            "function": entry.function,
            "line": entry.line,
            "instr_id": entry.instr_id,
            "action": entry.action,
            "before": entry.before,
            "after": entry.after,
        }
        for entry in opt_res.log
    ]

    opt_c = tac_to_c(opt_res.program)

    return make_envelope(
        warnings=sem_res.warnings,
        data={
            "functions": fn_names,
            "original": {"tac": tac_dict, "cfg": cfg_dict, "metrics": metrics_dict},
            "optimized": {"tac": opt_tac_dict, "cfg": opt_cfg_dict, "metrics": opt_metrics_dict},
            "log": log_entries,
            "optimized_c": opt_c,
            "warnings_dead_code": [],
        },
    )
