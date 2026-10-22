"""Comprehensive tests for Kushan's parser and AST builder (c2f.syntax).

Owner: Kushan.
Tests cover: all statements (var decl, if/else, while, do-while, for, switch/case,
return, break, continue), expressions, operators precedence, function definitions,
AST-to-JSON serialization, and panic-mode error recovery.
"""
import pytest

from c2f.lexer import tokenize
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
    ExprStmt,
    For,
    Function,
    Identifier,
    If,
    Literal,
    ParseResult,
    Program,
    Return,
    Switch,
    UnaryOp,
    VarDecl,
    While,
    ast_to_dict,
    parse,
)


def quick_parse(code: str) -> ParseResult:
    lex = tokenize(code)
    assert len(lex.errors) == 0, f"Lex errors: {lex.errors}"
    return parse(lex.tokens)


# ── Empty & Minimal ───────────────────────────────────────────────────
def test_empty_program():
    res = quick_parse("")
    assert res.errors == []
    assert res.ast is not None
    assert isinstance(res.ast, Program)
    assert res.ast.functions == []


def test_minimal_function():
    res = quick_parse("int main() { return 0; }")
    assert res.errors == []
    fn = res.ast.functions[0]
    assert fn.name == "main"
    assert fn.return_type == "int"
    assert fn.params == []
    assert len(fn.body.statements) == 1
    ret = fn.body.statements[0]
    assert isinstance(ret, Return)
    assert ret.value.value == "0"


def test_function_with_params():
    res = quick_parse("int add(int a, int b) { return a + b; }")
    assert res.errors == []
    fn = res.ast.functions[0]
    assert fn.name == "add"
    assert len(fn.params) == 2
    assert fn.params[0].name == "a" and fn.params[0].type == "int"
    assert fn.params[1].name == "b" and fn.params[1].type == "int"


# ── Variable Declarations ─────────────────────────────────────────────
def test_var_decl_without_init():
    res = quick_parse("void f() { int x; }")
    assert res.errors == []
    decl = res.ast.functions[0].body.statements[0]
    assert isinstance(decl, VarDecl)
    assert decl.name == "x"
    assert decl.var_type == "int"
    assert decl.init is None
    assert decl.array_size is None


def test_var_decl_with_init():
    res = quick_parse("void f() { float y = 3.14; }")
    assert res.errors == []
    decl = res.ast.functions[0].body.statements[0]
    assert isinstance(decl, VarDecl)
    assert decl.name == "y"
    assert decl.var_type == "float"
    assert isinstance(decl.init, Literal)
    assert decl.init.value == "3.14"


def test_array_decl():
    res = quick_parse("void f() { int arr[10]; }")
    assert res.errors == []
    decl = res.ast.functions[0].body.statements[0]
    assert isinstance(decl, VarDecl)
    assert decl.name == "arr"
    assert decl.array_size == 10


# ── Assignments & Expressions ─────────────────────────────────────────
def test_assignment():
    res = quick_parse("void f() { x = 42; }")
    assert res.errors == []
    stmt = res.ast.functions[0].body.statements[0]
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expr, Assign)
    assert stmt.expr.op == "="
    assert stmt.expr.target.name == "x"
    assert stmt.expr.value.value == "42"


def test_compound_assignments():
    res = quick_parse("void f() { x += 1; y -= 2; z *= 3; w /= 4; }")
    assert res.errors == []
    stmts = res.ast.functions[0].body.statements
    assert [s.expr.op for s in stmts] == ["+=", "-=", "*=", "/="]


# ── Control Flow ──────────────────────────────────────────────────────
def test_if_else():
    res = quick_parse("void f() { if (x > 0) { x = 1; } else { x = -1; } }")
    assert res.errors == []
    stmt = res.ast.functions[0].body.statements[0]
    assert isinstance(stmt, If)
    assert isinstance(stmt.cond, BinaryOp)
    assert stmt.cond.op == ">"
    assert isinstance(stmt.then, Block)
    assert isinstance(stmt.else_, Block)


def test_while_loop():
    res = quick_parse("void f() { while (i < 10) { i++; } }")
    assert res.errors == []
    stmt = res.ast.functions[0].body.statements[0]
    assert isinstance(stmt, While)
    assert stmt.cond.op == "<"
    assert isinstance(stmt.body, Block)


def test_do_while():
    res = quick_parse("void f() { do { i++; } while (i < 10); }")
    assert res.errors == []
    stmt = res.ast.functions[0].body.statements[0]
    assert isinstance(stmt, DoWhile)
    assert stmt.cond.op == "<"


def test_for_loop():
    res = quick_parse("void f() { for (int i = 0; i < 10; i++) { sum += i; } }")
    assert res.errors == []
    stmt = res.ast.functions[0].body.statements[0]
    assert isinstance(stmt, For)
    assert isinstance(stmt.init, VarDecl)
    assert isinstance(stmt.cond, BinaryOp)
    assert isinstance(stmt.update, UnaryOp)


def test_switch_case():
    src = """
    void f() {
        switch (x) {
            case 1:
                y = 10;
                break;
            default:
                y = 0;
                break;
        }
    }
    """
    res = quick_parse(src)
    assert res.errors == []
    stmt = res.ast.functions[0].body.statements[0]
    assert isinstance(stmt, Switch)
    assert len(stmt.cases) == 2
    assert stmt.cases[0].value is not None  # case 1
    assert stmt.cases[1].value is None      # default


def test_break_continue():
    src = "void f() { while (1) { break; continue; } }"
    res = quick_parse(src)
    assert res.errors == []
    stmts = res.ast.functions[0].body.statements[0].body.statements
    assert isinstance(stmts[0], Break)
    assert isinstance(stmts[1], Continue)


# ── Calls & I/O ───────────────────────────────────────────────────────
def test_function_call():
    src = 'void f() { printf("%d", x); scanf("%d", &y); }'
    res = quick_parse(src)
    assert res.errors == []
    stmts = res.ast.functions[0].body.statements
    assert isinstance(stmts[0].expr, Call)
    assert stmts[0].expr.name == "printf"
    assert len(stmts[0].expr.args) == 2
    assert isinstance(stmts[1].expr, Call)
    assert stmts[1].expr.name == "scanf"


# ── Precedence Climbing ───────────────────────────────────────────────
def test_precedence_mul_over_add():
    res = quick_parse("void f() { x = 2 + 3 * 4; }")
    assert res.errors == []
    val = res.ast.functions[0].body.statements[0].expr.value
    # 2 + (3 * 4)
    assert isinstance(val, BinaryOp)
    assert val.op == "+"
    assert val.left.value == "2"
    assert isinstance(val.right, BinaryOp)
    assert val.right.op == "*"


def test_precedence_logical():
    res = quick_parse("void f() { x = a || b && c; }")
    assert res.errors == []
    val = res.ast.functions[0].body.statements[0].expr.value
    # a || (b && c)
    assert val.op == "||"
    assert val.right.op == "&&"


def test_unary_and_postfix():
    res = quick_parse("void f() { x = -y; z = !flag; i++; ++j; }")
    assert res.errors == []
    stmts = res.ast.functions[0].body.statements
    assert stmts[0].expr.value.op == "-"
    assert stmts[1].expr.value.op == "!"
    assert stmts[2].expr.op == "++" and stmts[2].expr.postfix is True
    assert stmts[3].expr.op == "++" and stmts[3].expr.postfix is False


def test_array_access():
    res = quick_parse("void f() { x = arr[i + 1]; }")
    assert res.errors == []
    val = res.ast.functions[0].body.statements[0].expr.value
    assert isinstance(val, ArrayAccess)
    assert val.name == "arr"
    assert isinstance(val.index, BinaryOp)


# ── AST JSON Serialization ────────────────────────────────────────────
def test_ast_to_dict():
    res = quick_parse("int main() { if (x > 0) { return 1; } else { return 0; } }")
    d = ast_to_dict(res.ast)
    assert d["type"] == "Program"
    assert "line" in d and "col" in d
    assert len(d["functions"]) == 1
    fn = d["functions"][0]
    assert fn["type"] == "Function"
    assert fn["name"] == "main"
    assert fn["return_type"] == "int"
    if_stmt = fn["body"]["statements"][0]
    assert if_stmt["type"] == "If"
    assert "else" in if_stmt  # key is "else", not "else_"
    assert if_stmt["else"]["type"] == "Block"


# ── Panic-Mode Error Recovery ─────────────────────────────────────────
def test_error_recovery_missing_semi():
    toks = tokenize("void f() { int x\nint y = 5; }")
    res = parse(toks.tokens)
    assert len(res.errors) >= 1
    assert any(";" in e.message for e in res.errors)
    # Parser should have recovered and parsed the second declaration
    fn = res.ast.functions[0]
    names = [s.name for s in fn.body.statements if isinstance(s, VarDecl)]
    assert "y" in names


def test_error_recovery_bad_condition():
    toks = tokenize("void f() { if x > 0 { y = 1; } int z = 2; }")
    res = parse(toks.tokens)
    assert len(res.errors) >= 1
    assert res.errors[0].phase == "parser"
