"""FastAPI app: routes only. All logic lives in c2f.pipeline. Owner: Raghav.

Run from the backend/ folder:  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from c2f.common import make_error
from c2f.pipeline import make_envelope, run_ast, run_pipeline, run_tokens

app = FastAPI(title="code2flow API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CompileRequest(BaseModel):
    language: str = "c"
    code: str


def _handle(req: CompileRequest, run: Callable[[str], dict]) -> dict:
    """Compile errors are HTTP 200 with ok=false (CONTRACTS.md section 8)."""
    if req.language.strip().lower() != "c":
        return make_envelope([make_error("parser", f"Unsupported language: {req.language!r} (only 'c')", 1, 1)])
    return run(req.code)


@app.post("/api/tokens")
def tokens(req: CompileRequest) -> dict:
    return _handle(req, run_tokens)


@app.post("/api/ast")
def ast(req: CompileRequest) -> dict:
    return _handle(req, run_ast)


@app.post("/api/generate")
def generate(req: CompileRequest) -> dict:
    return _handle(req, lambda code: run_pipeline(code, optimize=False))


@app.post("/api/optimize")
def optimize(req: CompileRequest) -> dict:
    return _handle(req, lambda code: run_pipeline(code, optimize=True))
