"""c2f.syntax — parser, AST nodes, AST-to-JSON.  Owner: Kushan."""

from .ast_json import ast_to_dict
from .ast_nodes import (
    ArrayAccess,
    Assign,
    BinaryOp,
    Block,
    Break,
    Call,
    Case,
    Continue,
    DoWhile,
    Expr,
    ExprStmt,
    For,
    Function,
    Identifier,
    If,
    Literal,
    Node,
    Param,
    Program,
    Return,
    Stmt,
    Switch,
    UnaryOp,
    VarDecl,
    While,
)
from .parser import ParseResult, parse

__all__ = [
    "parse", "ParseResult", "ast_to_dict",
    # base
    "Node", "Stmt", "Expr",
    # top-level
    "Program", "Function", "Param",
    # statements
    "Block", "VarDecl", "ExprStmt", "If", "While", "DoWhile", "For",
    "Switch", "Case", "Return", "Break", "Continue",
    # expressions
    "Assign", "BinaryOp", "UnaryOp", "Literal", "Identifier", "ArrayAccess", "Call",
]
