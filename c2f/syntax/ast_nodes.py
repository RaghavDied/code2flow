"""AST node classes (CONTRACTS.md section 5). Owner: Kushan.

Every node is a dataclass with ``line: int`` and ``col: int`` (1-based).
Operators are source strings (``"+"``, ``"=="``, ``"&&"``, ``"!"``, ``"++"``, …).
Absent optional children are ``None``.  Lists default to ``[]``.

Integration Contract with Raghav (Semantic Checker & Diagnostics)
-----------------------------------------------------------------
1. Diagnostic Format (diagnostics.py):
   Kushan uses Raghav's Diagnostic dataclass to report lexical and syntax errors
   with 1-based line and col so errors display uniformly across the whole application.

2. AST Validation:
   Kushan's AST node dataclasses are validated and annotated by Raghav's semantic
   checker (analyze). Expression nodes support in-place `.expr_type` annotation
   ("int" | "float" | "char" | "void" | "string") without exposing it in dataclass
   fields or AST JSON output.

Hierarchy
---------
Node
├── Stmt   (Block, VarDecl, ExprStmt, If, While, DoWhile, For, Switch,
│           Return, Break, Continue)
├── Expr   (Assign, BinaryOp, UnaryOp, Literal, Identifier, ArrayAccess, Call)
│           — all Expr nodes carry a mutable ``expr_type`` attribute
│             (set to ``None`` until the semantic pass annotates it)
├── Case   (used inside Switch)
├── Function
└── Program

``Param`` is a plain dataclass for function parameters (not a Node).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ── base classes ──────────────────────────────────────────────────────
@dataclass
class Node:
    """Every AST node carries its 1-based source position."""
    line: int
    col: int


@dataclass
class Stmt(Node):
    """Base class of all statement nodes."""


@dataclass
class Expr(Node):
    """Base class of all expression nodes.

    ``expr_type`` is a *plain class attribute* (not a dataclass field) so it
    never appears in ``dataclasses.fields()`` or in the AST JSON.  The
    semantic pass sets it to ``"int"`` | ``"float"`` | ``"char"`` |
    ``"void"`` | ``"string"`` per node.
    """
    # Not annotated ⇒ not a dataclass field.  Each instance gets its own
    # copy when the semantic pass writes to it (instance attr shadows class attr).
    expr_type = None


# ── expressions ───────────────────────────────────────────────────────
@dataclass
class Literal(Expr):
    """A literal value: int, float, char, or string."""
    value: str = ""
    literal_type: str = "int"   # "int" | "float" | "char" | "string"


@dataclass
class Identifier(Expr):
    """A variable or function name reference."""
    name: str = ""


@dataclass
class ArrayAccess(Expr):
    """arr[index]."""
    name: str = ""
    index: Optional[Expr] = None


@dataclass
class BinaryOp(Expr):
    """left op right.  op is the source string ('+', '==', '&&', …)."""
    op: str = ""
    left: Optional[Expr] = None
    right: Optional[Expr] = None


@dataclass
class UnaryOp(Expr):
    """op operand.  op is '-', '!', '++', '--', or '&'.  postfix=True for x++/x--."""
    op: str = ""
    operand: Optional[Expr] = None
    postfix: bool = False


@dataclass
class Call(Expr):
    """function_name(args)."""
    name: str = ""
    args: List[Expr] = field(default_factory=list)


@dataclass
class Assign(Expr):
    """target op value.  op is '=', '+=', '-=', '*=', '/='."""
    target: Optional[Expr] = None          # Identifier | ArrayAccess
    op: str = "="
    value: Optional[Expr] = None


# ── statements ────────────────────────────────────────────────────────
@dataclass
class ExprStmt(Stmt):
    """An expression used as a statement (e.g. function call, assignment)."""
    expr: Optional[Expr] = None


@dataclass
class VarDecl(Stmt):
    """Variable (or array) declaration with optional initialiser."""
    var_type: str = ""
    name: str = ""
    array_size: Optional[int] = None
    init: Optional[Expr] = None


@dataclass
class Block(Stmt):
    """``{ statements }``."""
    statements: List[Stmt] = field(default_factory=list)


@dataclass
class If(Stmt):
    """``if (cond) then [else else_]``."""
    cond: Optional[Expr] = None
    then: Optional[Stmt] = None
    else_: Optional[Stmt] = None           # JSON key: "else"


@dataclass
class While(Stmt):
    """``while (cond) body``."""
    cond: Optional[Expr] = None
    body: Optional[Stmt] = None


@dataclass
class DoWhile(Stmt):
    """``do body while (cond);``"""
    body: Optional[Stmt] = None
    cond: Optional[Expr] = None


@dataclass
class For(Stmt):
    """``for (init; cond; update) body``."""
    init: Optional[Stmt] = None
    cond: Optional[Expr] = None
    update: Optional[Expr] = None
    body: Optional[Stmt] = None


@dataclass
class Case(Node):
    """One case/default arm in a switch.  value is ``None`` for default."""
    value: Optional[Expr] = None
    body: List[Stmt] = field(default_factory=list)


@dataclass
class Switch(Stmt):
    """``switch (expr) { cases }``."""
    expr: Optional[Expr] = None
    cases: List[Case] = field(default_factory=list)


@dataclass
class Return(Stmt):
    """``return [value];``"""
    value: Optional[Expr] = None


@dataclass
class Break(Stmt):
    """``break;``"""
    pass


@dataclass
class Continue(Stmt):
    """``continue;``"""
    pass


# ── top-level ─────────────────────────────────────────────────────────
@dataclass
class Param:
    """A function parameter ``{type, name}``.  Not a Node (no separate line/col)."""
    type: str = ""
    name: str = ""


@dataclass
class Function(Node):
    """A function definition."""
    name: str = ""
    return_type: str = "void"              # "int" | "float" | "char" | "void"
    params: List[Param] = field(default_factory=list)
    body: Optional[Block] = None


@dataclass
class Program(Node):
    """The root: a list of functions."""
    functions: List[Function] = field(default_factory=list)
