"""AST node classes (CONTRACTS section 5).

Every node has `line` and `col` (1-based). Construct nodes with keyword arguments.
Expression nodes also get a plain Python attribute `expr_type` (set later by the
semantic pass). It is deliberately NOT a dataclass field, so it never appears in
the AST JSON.
"""

from dataclasses import dataclass
from typing import Optional


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

    statements: list[Stmt]


@dataclass
class Function(Node):
    """Function definition. params is a list of {"type": str, "name": str}."""

    name: str
    return_type: str  # "int" | "float" | "char" | "void"
    params: list[dict[str, str]]
    body: Block


@dataclass
class Program(Node):
    """Whole translation unit."""

    functions: list[Function]


# --------------------------------------------------------------- statements
@dataclass
class VarDecl(Stmt):
    """Variable or array declaration, optional initialiser."""

    var_type: str
    name: str
    array_size: Optional[int]
    init: Optional[Expr]


@dataclass
class ExprStmt(Stmt):
    """Expression used as a statement (assignment, call, i++ ...)."""

    expr: Expr


@dataclass
class If(Stmt):
    cond: Expr
    then: Stmt
    else_: Optional[Stmt]  # serialised under the JSON key "else"


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
    body: list[Stmt]


@dataclass
class Switch(Stmt):
    expr: Expr
    cases: list[Case]


@dataclass
class Return(Stmt):
    value: Optional[Expr]


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
    postfix: bool


@dataclass
class Assign(Expr):
    target: Expr  # Identifier | ArrayAccess
    op: str  # "=" | "+=" | "-=" | "*=" | "/="
    value: Expr


@dataclass
class Call(Expr):
    name: str
    args: list[Expr]
