"""Semantic analysis pass (CONTRACTS.md section 5).

Owner: Raghav.
Checks symbol declarations, scopes, types, loop context (break/continue),
and annotates expression nodes with `.expr_type`. Never crashes on bad input;
returns Diagnostic errors/warnings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from c2f.common import Diagnostic, make_error, make_warning

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
    Program,
    Return,
    Stmt,
    Switch,
    UnaryOp,
    VarDecl,
    While,
)
from .symbol_table import Symbol, SymbolTable

NUMERIC_TYPES = {"int", "float", "char"}
COMPARISON_OPS = {"<", "<=", ">", ">=", "==", "!=", "&&", "||"}


@dataclass
class SemanticResult:
    """Outcome of semantic analysis."""

    ast: Optional[Program] = None
    errors: List[Diagnostic] = field(default_factory=list)
    warnings: List[Diagnostic] = field(default_factory=list)


class SemanticChecker:
    """Traverses an AST, records Diagnostics, and annotates Expr.expr_type."""

    def __init__(self) -> None:
        self.symbols = SymbolTable()
        self.errors: List[Diagnostic] = []
        self.warnings: List[Diagnostic] = []
        self.loop_depth: int = 0
        self.switch_depth: int = 0
        self.current_function: Optional[Function] = None

    def error(self, msg: str, line: int, col: int) -> None:
        self.errors.append(make_error("semantic", msg, line, col))

    def warning(self, msg: str, line: int, col: int) -> None:
        self.warnings.append(make_warning("semantic", msg, line, col))

    def check_program(self, prog: Program) -> SemanticResult:
        if not hasattr(prog, "functions") or not isinstance(prog.functions, list):
            self.error("Malformed program AST: missing functions list", getattr(prog, "line", 1), getattr(prog, "col", 1))
            return SemanticResult(ast=prog, errors=self.errors, warnings=self.warnings)

        # First pass: register all functions globally
        for fn in prog.functions:
            if not isinstance(fn, Function):
                continue
            sym = Symbol(
                name=fn.name,
                type=fn.return_type,
                line=fn.line,
                col=fn.col,
                is_function=True,
                params=list(fn.params),
            )
            if not self.symbols.define(sym):
                self.error(f"Redeclaration of function '{fn.name}'", fn.line, fn.col)

        # Second pass: check function bodies
        for fn in prog.functions:
            if isinstance(fn, Function):
                self.check_function(fn)

        return SemanticResult(ast=prog, errors=self.errors, warnings=self.warnings)

    def check_function(self, fn: Function) -> None:
        self.current_function = fn
        self.symbols.enter_scope()

        # Define parameters in function scope
        seen_params = set()
        for p in fn.params:
            p_type = p.get("type", "int")
            p_name = p.get("name", "")
            if not p_name:
                continue
            if p_name in seen_params:
                self.error(f"Duplicate parameter '{p_name}' in function '{fn.name}'", fn.line, fn.col)
            else:
                seen_params.add(p_name)
                self.symbols.define(Symbol(name=p_name, type=p_type, line=fn.line, col=fn.col))

        if isinstance(fn.body, Block):
            self.check_block(fn.body, new_scope=False)
        elif fn.body is not None:
            self.check_stmt(fn.body)

        self.symbols.exit_scope()
        self.current_function = None

    def check_block(self, block: Block, new_scope: bool = True) -> None:
        if new_scope:
            self.symbols.enter_scope()

        for stmt in getattr(block, "statements", []):
            self.check_stmt(stmt)

        if new_scope:
            self.symbols.exit_scope()

    def check_stmt(self, stmt: Stmt) -> None:
        if stmt is None:
            return

        if isinstance(stmt, Block):
            self.check_block(stmt, new_scope=True)
        elif isinstance(stmt, VarDecl):
            self.check_var_decl(stmt)
        elif isinstance(stmt, ExprStmt):
            if stmt.expr:
                self.check_expr(stmt.expr)
        elif isinstance(stmt, If):
            self.check_if(stmt)
        elif isinstance(stmt, While):
            self.check_while(stmt)
        elif isinstance(stmt, DoWhile):
            self.check_do_while(stmt)
        elif isinstance(stmt, For):
            self.check_for(stmt)
        elif isinstance(stmt, Switch):
            self.check_switch(stmt)
        elif isinstance(stmt, Return):
            self.check_return(stmt)
        elif isinstance(stmt, Break):
            if self.loop_depth == 0 and self.switch_depth == 0:
                self.error("'break' statement not within loop or switch", stmt.line, stmt.col)
        elif isinstance(stmt, Continue):
            if self.loop_depth == 0:
                self.error("'continue' statement not within a loop", stmt.line, stmt.col)

    def check_var_decl(self, decl: VarDecl) -> None:
        sym = Symbol(
            name=decl.name,
            type=decl.var_type,
            line=decl.line,
            col=decl.col,
            is_array=decl.array_size is not None,
            array_size=decl.array_size,
        )
        if not self.symbols.define(sym):
            self.error(f"Redeclaration of variable '{decl.name}' in the same scope", decl.line, decl.col)

        if decl.init is not None:
            init_type = self.check_expr(decl.init)
            if decl.var_type != init_type and not (decl.var_type in NUMERIC_TYPES and init_type in NUMERIC_TYPES):
                self.warning(
                    f"Type mismatch initializing '{decl.name}' ({decl.var_type}) with expression of type '{init_type}'",
                    decl.line,
                    decl.col,
                )

    def check_if(self, node: If) -> None:
        self.check_expr(node.cond)
        self.check_stmt(node.then)
        if node.else_ is not None:
            self.check_stmt(node.else_)

    def check_while(self, node: While) -> None:
        self.check_expr(node.cond)
        self.loop_depth += 1
        self.check_stmt(node.body)
        self.loop_depth -= 1

    def check_do_while(self, node: DoWhile) -> None:
        self.loop_depth += 1
        self.check_stmt(node.body)
        self.loop_depth -= 1
        self.check_expr(node.cond)

    def check_for(self, node: For) -> None:
        self.symbols.enter_scope()
        if node.init is not None:
            self.check_stmt(node.init)
        if node.cond is not None:
            self.check_expr(node.cond)
        self.loop_depth += 1
        self.check_stmt(node.body)
        self.loop_depth -= 1
        if node.update is not None:
            self.check_expr(node.update)
        self.symbols.exit_scope()

    def check_switch(self, node: Switch) -> None:
        self.check_expr(node.expr)
        self.switch_depth += 1
        for case in getattr(node, "cases", []):
            if case.value is not None:
                self.check_expr(case.value)
            for stmt in getattr(case, "body", []):
                self.check_stmt(stmt)
        self.switch_depth -= 1

    def check_return(self, node: Return) -> None:
        ret_type = self.check_expr(node.value) if node.value is not None else "void"
        expected = self.current_function.return_type if self.current_function else "void"

        if expected == "void" and ret_type != "void":
            self.error("Void function should not return a value", node.line, node.col)
        elif expected != "void" and ret_type == "void":
            self.warning(f"Function returning '{expected}' has empty return statement", node.line, node.col)

    def check_expr(self, expr: Optional[Expr]) -> str:
        if expr is None:
            return "void"

        t = "int"  # fallback
        if isinstance(expr, Literal):
            t = expr.literal_type
        elif isinstance(expr, Identifier):
            sym = self.symbols.lookup(expr.name)
            if sym is None:
                self.error(f"Use of undeclared identifier '{expr.name}'", expr.line, expr.col)
                t = "int"
            else:
                t = sym.type
        elif isinstance(expr, ArrayAccess):
            sym = self.symbols.lookup(expr.name)
            if sym is None:
                self.error(f"Use of undeclared array '{expr.name}'", expr.line, expr.col)
                t = "int"
            else:
                t = sym.type
            idx_t = self.check_expr(expr.index)
            if idx_t not in ("int", "char"):
                self.error(f"Array index must be an integer, got '{idx_t}'", expr.line, expr.col)
        elif isinstance(expr, Assign):
            target_t = self.check_expr(expr.target)
            val_t = self.check_expr(expr.value)
            if target_t != val_t and not (target_t in NUMERIC_TYPES and val_t in NUMERIC_TYPES):
                self.warning(f"Type mismatch in assignment: '{target_t}' {expr.op} '{val_t}'", expr.line, expr.col)
            t = target_t
        elif isinstance(expr, BinaryOp):
            l_t = self.check_expr(expr.left)
            r_t = self.check_expr(expr.right)
            if expr.op in COMPARISON_OPS:
                t = "int"
            elif expr.op == "%":
                if l_t not in ("int", "char") or r_t not in ("int", "char"):
                    self.error("Operator '%' requires integer operands", expr.line, expr.col)
                t = "int"
            elif "float" in (l_t, r_t):
                t = "float"
            else:
                t = "int"
        elif isinstance(expr, UnaryOp):
            op_t = self.check_expr(expr.operand)
            if expr.op == "!":
                t = "int"
            elif expr.op == "&":
                t = op_t
            else:
                t = op_t
        elif isinstance(expr, Call):
            sym = self.symbols.lookup(expr.name)
            if sym is None:
                self.error(f"Call to undeclared function '{expr.name}'", expr.line, expr.col)
                t = "int"
            elif not sym.is_function:
                self.error(f"'{expr.name}' is not a function", expr.line, expr.col)
                t = "int"
            else:
                t = sym.type
                # Check arguments count (printf/scanf are variadic builtins)
                if expr.name not in ("printf", "scanf") and len(expr.args) != len(sym.params):
                    self.error(
                        f"Function '{expr.name}' expects {len(sym.params)} argument(s), got {len(expr.args)}",
                        expr.line,
                        expr.col,
                    )
            for a in expr.args:
                self.check_expr(a)

        expr.expr_type = t
        return t


def analyze(ast: Program) -> SemanticResult:
    """Annotate expression nodes with .expr_type and report scope/type errors."""
    checker = SemanticChecker()
    return checker.check_program(ast)
