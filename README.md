# code2flow

Compiler-based Code-to-Flowchart Generator with Code Optimisation (Compiler Design project).
C source -> lexer -> parser -> AST -> semantic analysis -> three-address code -> optimiser ->
control flow graph -> interactive flowchart (original and optimised).

Names, folders, formats and signatures are fixed in **[CONTRACTS.md](CONTRACTS.md)**. Read it first.

## Who owns what

| Owner | Folders |
| --- | --- |
| Kushan | `backend/c2f/lexer/`, `backend/c2f/syntax/`, tests `test_lexer_*`, `test_syntax_*`, samples 01-19 |
| Raghav | repo skeleton, `backend/main.py`, `c2f/common/`, `semantic/`, `ir/`, `cfg/`, `metrics/`, `pipeline.py`, tests `test_semantic_*`, `test_ir_*`, `test_cfg_*`, samples 20-39 |
| Ishani | `backend/c2f/optimizer/`, `backend/tests/fixtures/tac/`, tests `test_optimizer_*`, samples 40-59 |
| Sneh | everything under `frontend/`, samples 60-79 |

Only edit files you own. Shared: `backend/requirements.txt` (append-only) and your number range in `samples/`.

## Run the backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Until the real stages land, `c2f/pipeline.py` has `USE_MOCKS = True` and every endpoint returns the
fixtures from `backend/tests/fixtures/`. Unbalanced `(` `)` or `{` `}` in the code returns the
error fixture, so the UI can test its error panel.

## Run the tests

From the repo root:

```bash
pip install -r backend/requirements.txt
pytest backend/tests
```

## Run the frontend (Sneh)

Vite dev server on http://localhost:5173. Set `VITE_API_URL` (default `http://localhost:8000`).
Develop against `frontend/src/mocks/*.json`; they are copies of the backend fixtures.

## Git workflow

- `main` is always runnable. Nobody pushes to `main` directly.
- Branches: `feature/<yourname>-<module>` (e.g. `feature/ishani-const-prop`).
- One small PR per finished piece; a teammate reviews before merge.
- Commit messages: `<module>: <what>` (e.g. `lexer: add comment skipping`).
- Run `pytest backend/tests` before opening a PR. A red suite blocks merge.
- `CONTRACTS.md`, `c2f/common/` and `backend/requirements.txt` change only via a PR that names every
  affected teammate. Announce contract changes in the group chat BEFORE coding them.
- If you hit a merge conflict, you edited someone else's file. Revert that edit and message the owner.

## Repo layout

```
backend/main.py            FastAPI routes only
backend/c2f/               all compiler code (lexer, syntax, semantic, ir, cfg, optimizer, metrics, pipeline)
backend/tests/             pytest tests + fixtures/
frontend/                  React + Vite + React Flow app
samples/                   shared C test programs: NN_short_name.c, *_err.c = invalid syntax
```
