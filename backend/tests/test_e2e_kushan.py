"""End-to-end tests for Kushan's front end (samples 01 to 19).

Owner: Kushan.
Tests every sample file in Kushan's allocated range (01-19):
- Valid samples must parse with 0 errors and produce a valid AST.
- Invalid samples (*_err.c) must record at least 1 Diagnostic error without crashing.
"""
from pathlib import Path
import pytest

from c2f.lexer import tokenize
from c2f.syntax import ast_to_dict, parse

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"


def get_kushan_samples():
    """Return all .c files in samples/ matching 01-19."""
    samples = sorted(SAMPLES_DIR.glob("[0-1][0-9]_*.c"))
    return samples


@pytest.mark.parametrize("sample_path", get_kushan_samples(), ids=lambda p: p.name)
def test_sample_file(sample_path: Path):
    source = sample_path.read_text(encoding="utf-8")
    is_err_case = sample_path.name.endswith("_err.c")

    lex_res = tokenize(source)
    parse_res = parse(lex_res.tokens)

    all_errors = lex_res.errors + parse_res.errors

    if is_err_case:
        # Must report at least one syntax error and NEVER crash
        assert len(all_errors) > 0, f"Expected errors in invalid sample {sample_path.name}, got none"
        for err in all_errors:
            assert err.phase in ("lexer", "parser")
            assert err.severity == "error"
            assert err.line >= 1
            assert err.col >= 1
    else:
        # Valid C code in supported subset must parse cleanly
        assert len(all_errors) == 0, f"Unexpected errors in {sample_path.name}: {all_errors}"
        assert parse_res.ast is not None
        # Must successfully serialize to dict
        d = ast_to_dict(parse_res.ast)
        assert d["type"] == "Program"
        assert len(d["functions"]) >= 1
