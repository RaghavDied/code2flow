"""Pipeline wiring (CONTRACTS.md section 8). Owner: Raghav.

While the real stages are being built, USE_MOCKS is True and every function returns
the JSON fixtures in backend/tests/fixtures, so Sneh can build the UI against the real
endpoints. Flip USE_MOCKS to False once tokenize/parse/analyze/generate_tac/build_cfg/
optimize are all implemented.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from c2f.common import Diagnostic, make_error

USE_MOCKS = True
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

    Empty source, or unbalanced ( ) / { }, returns an error envelope. Removed with the mocks.
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
    raise NotImplementedError("real lexer pipeline not wired yet")


def run_ast(source: str) -> dict:
    """POST /api/ast."""
    if USE_MOCKS:
        return _mock_gate(source) or _load("ast_ok")
    raise NotImplementedError("real parser pipeline not wired yet")


def run_pipeline(source: str, optimize: bool = False) -> dict:
    """POST /api/generate (optimize=False) and POST /api/optimize (optimize=True)."""
    if USE_MOCKS:
        return _mock_gate(source) or _load("optimize_ok" if optimize else "generate_ok")
    raise NotImplementedError("real pipeline not wired yet")
