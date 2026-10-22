"""AST node classes used by semantic and IR passes (CONTRACTS.md section 5).

Owner: Raghav (in semantic/ to remain independent of syntax/ state until Kushan merges).
Every node has `line` and `col` (1-based). Expression nodes have `.expr_type` set
by the semantic analysis pass.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Node:
    """Base class of all AST nodes."""

    line: int
    col: int


@dataclass
class Stmt(Node):
    """Base class of statement nodes."""


@dataclass
class Expr(Node):
    """Base class of expression nodes."""

    # Plain class attribute (no annotation => not a dataclass field).
    # Semantic pass sets "int" | "float" | "char" | "void" | "string".
    expr_type = None


# ---------------------------------------------------------------- top level
@dataclass
class Block(Stmt):
    """`{ statements }`"""

    statements: List[Stmt]


@dataclass
class Function(Node):
    """Function definition. params is a list of {"type": str, "name": str}."""

    name: str
    return_type: str  # "int" | "float" | "char" | "void"
    params: List[dict]
    body: Block


@dataclass
class Program(Node):
    """Whole translation unit."""

    functions: List[Function]


# --------------------------------------------------------------- statements
@dataclass
class VarDecl(Stmt):
    """Variable or array declaration, optional initialiser."""

    var_type: str
    name: str
    array_size: Optional[int] = None
    init: Optional[Expr] = None


@dataclass
class ExprStmt(Stmt):
    """Expression used as a statement."""

    expr: Expr


@dataclass
class If(Stmt):
    cond: Expr
    then: Stmt
    else_: Optional[Stmt] = None  # serialised under the JSON key "else"


@dataclass
class While(Stmt):
    cond: Expr
    body: Stmt


@dataclass
class DoWhile(Stmt):
    body: Stmt
    cond: Expr


@dataclass
class For(Stmt):
    init: Optional[Stmt]
    cond: Optional[Expr]
    update: Optional[Expr]
    body: Stmt


@dataclass
class Case(Node):
    """One switch case. value None means `default`."""

    value: Optional[Expr]
    body: List[Stmt]


@dataclass
class Switch(Stmt):
    expr: Expr
    cases: List[Case]


@dataclass
class Return(Stmt):
    value: Optional[Expr] = None


@dataclass
class Break(Stmt):
    pass


@dataclass
class Continue(Stmt):
    pass


# -------------------------------------------------------------- expressions
@dataclass
class Identifier(Expr):
    name: str


@dataclass
class ArrayAccess(Expr):
    name: str
    index: Expr


@dataclass
class Literal(Expr):
    """Literal kept as its source text."""

    value: str
    literal_type: str  # "int" | "float" | "char" | "string"


@dataclass
class BinaryOp(Expr):
    op: str  # + - * / % < <= > >= == != && ||
    left: Expr
    right: Expr


@dataclass
class UnaryOp(Expr):
    op: str  # "-" | "!" | "++" | "--" | "&"
    operand: Expr
    postfix: bool = False


@dataclass
class Assign(Expr):
    target: Expr  # Identifier | ArrayAccess
    op: str  # "=" | "+=" | "-=" | "*=" | "/="
    value: Expr


@dataclass
class Call(Expr):
    name: str
    args: List[Expr]
