"""AST node classes (CONTRACTS.md section 5). Owner: Kushan.
# SKELETON STUB created by Raghav. The owner replaces this file; keep the public names/signatures from CONTRACTS.md. Add every node class from section 5 and export it from syntax/__init__.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Node:
    """Every node carries its 1-based source position."""

    line: int
    col: int


@dataclass
class Program(Node):
    functions: List[Node] = field(default_factory=list)
