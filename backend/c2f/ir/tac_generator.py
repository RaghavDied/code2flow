"""AST -> TAC lowering. Owner: Raghav. TODO (Week 2): implement per CONTRACTS.md section 6."""
from __future__ import annotations

from c2f.syntax import Program

from .tac import TacProgram


def generate_tac(ast: Program) -> TacProgram:
    """Lower an analysed AST to three-address code."""
    raise NotImplementedError("generate_tac is not implemented yet (Raghav, Week 2)")
