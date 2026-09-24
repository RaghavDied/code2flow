"""Recursive-descent parser. Owner: Kushan.
# SKELETON STUB created by Raghav. The owner replaces this file; keep the public names/signatures from CONTRACTS.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from c2f.common import Diagnostic
from c2f.lexer import Token

from .ast_nodes import Program


@dataclass
class ParseResult:
    ast: Optional[Program] = None
    errors: List[Diagnostic] = field(default_factory=list)


def parse(tokens: List[Token]) -> ParseResult:
    raise NotImplementedError("parse is not implemented yet (Kushan)")
