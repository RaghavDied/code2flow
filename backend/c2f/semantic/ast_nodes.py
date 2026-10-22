"""Re-export AST node classes from c2f.syntax for backward compatibility."""
from c2f.syntax import (
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
    Program,
    Return,
    Stmt,
    Switch,
    UnaryOp,
    VarDecl,
    While,
)

__all__ = [
    "Node", "Stmt", "Expr", "Block", "Function", "Program",
    "VarDecl", "ExprStmt", "If", "While", "DoWhile", "For", "Case",
    "Switch", "Return", "Break", "Continue",
    "Identifier", "ArrayAccess", "Literal", "BinaryOp", "UnaryOp", "Assign", "Call",
]
