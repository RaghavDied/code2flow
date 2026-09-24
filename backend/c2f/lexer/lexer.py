"""Hand-written lexer. Owner: Kushan.
# SKELETON STUB created by Raghav. The owner replaces this file; keep the public names/signatures from CONTRACTS.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from c2f.common import Diagnostic

from .tokens import Token


@dataclass
class LexResult:
    tokens: List[Token] = field(default_factory=list)
    errors: List[Diagnostic] = field(default_factory=list)


def tokenize(source: str) -> LexResult:
    """Never raises on bad input; records a Diagnostic and continues."""
    raise NotImplementedError("tokenize is not implemented yet (Kushan)")
