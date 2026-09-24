"""Semantic checks (CONTRACTS.md section 5). Owner: Raghav. TODO (Week 2)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from c2f.common import Diagnostic
from c2f.syntax import Program


@dataclass
class SemanticResult:
    ast: Optional[Program] = None
    errors: List[Diagnostic] = field(default_factory=list)
    warnings: List[Diagnostic] = field(default_factory=list)


def analyze(ast: Program) -> SemanticResult:
    """Annotate expression nodes with .expr_type and report scope/type errors."""
    raise NotImplementedError("analyze is not implemented yet (Raghav, Week 2)")
