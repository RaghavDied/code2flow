"""Comprehensive tests for Kushan's lexer (c2f.lexer).

Owner: Kushan.
Tests cover: keywords, literals, operators, punctuation, comments,
preprocessor skipping, line/col tracking, and error diagnostics.
"""
import pytest

from c2f.common import Diagnostic
from c2f.lexer import LexResult, Token, TokenType, tokenize
from c2f.lexer.tokens import KEYWORDS


# ── Basic & Empty ─────────────────────────────────────────────────────
def test_empty_source():
    res = tokenize("")
    assert len(res.tokens) == 1
    assert res.tokens[0].type == TokenType.EOF
    assert res.errors == []


def test_whitespace_only():
    res = tokenize("   \t  \n  \r\n  ")
    assert len(res.tokens) == 1
    assert res.tokens[0].type == TokenType.EOF
    assert res.errors == []


# ── Keywords ──────────────────────────────────────────────────────────
def test_all_15_keywords():
    src = "int float char void if else while do for switch case default break continue return"
    res = tokenize(src)
    assert len(res.errors) == 0
    types = [t.type for t in res.tokens[:-1]]  # exclude EOF
    expected = [
        TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_CHAR, TokenType.KW_VOID,
        TokenType.KW_IF, TokenType.KW_ELSE, TokenType.KW_WHILE, TokenType.KW_DO,
        TokenType.KW_FOR, TokenType.KW_SWITCH, TokenType.KW_CASE, TokenType.KW_DEFAULT,
        TokenType.KW_BREAK, TokenType.KW_CONTINUE, TokenType.KW_RETURN,
    ]
    assert types == expected


def test_keywords_dict():
    assert len(KEYWORDS) == 15
    for kw, tt in KEYWORDS.items():
        res = tokenize(kw)
        assert res.tokens[0].type == tt
        assert res.tokens[0].lexeme == kw


# ── Identifiers ───────────────────────────────────────────────────────
def test_identifiers():
    src = "foo bar_baz _leadingVar x123 camelCase"
    res = tokenize(src)
    assert len(res.errors) == 0
    names = [t.lexeme for t in res.tokens[:-1]]
    assert names == ["foo", "bar_baz", "_leadingVar", "x123", "camelCase"]
    for t in res.tokens[:-1]:
        assert t.type == TokenType.IDENTIFIER


# ── Literals ──────────────────────────────────────────────────────────
def test_int_literals():
    src = "0 42 123456789"
    res = tokenize(src)
    assert len(res.errors) == 0
    assert [t.lexeme for t in res.tokens[:-1]] == ["0", "42", "123456789"]
    for t in res.tokens[:-1]:
        assert t.type == TokenType.INT_LITERAL


def test_float_literals():
    src = "3.14 0.5 123.456"
    res = tokenize(src)
    assert len(res.errors) == 0
    assert [t.lexeme for t in res.tokens[:-1]] == ["3.14", "0.5", "123.456"]
    for t in res.tokens[:-1]:
        assert t.type == TokenType.FLOAT_LITERAL


def test_string_literals():
    src = r'"hello world" "escaped \"quotes\"" "with\nnewlines"'
    res = tokenize(src)
    assert len(res.errors) == 0
    for t in res.tokens[:-1]:
        assert t.type == TokenType.STRING_LITERAL


def test_char_literals():
    src = r"'a' 'Z' '\n' '\0' '\''"
    res = tokenize(src)
    assert len(res.errors) == 0
    for t in res.tokens[:-1]:
        assert t.type == TokenType.CHAR_LITERAL


# ── Operators ─────────────────────────────────────────────────────────
def test_all_operators():
    src = "+ - * / % = += -= *= /= ++ -- == != < <= > >= && || ! &"
    res = tokenize(src)
    assert len(res.errors) == 0
    expected = [
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT,
        TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN, TokenType.STAR_ASSIGN,
        TokenType.SLASH_ASSIGN, TokenType.INC, TokenType.DEC, TokenType.EQ, TokenType.NE,
        TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE, TokenType.AND, TokenType.OR,
        TokenType.NOT, TokenType.AMP,
    ]
    assert [t.type for t in res.tokens[:-1]] == expected


# ── Punctuation ───────────────────────────────────────────────────────
def test_all_punctuation():
    src = "( ) { } [ ] ; , :"
    res = tokenize(src)
    assert len(res.errors) == 0
    expected = [
        TokenType.LPAREN, TokenType.RPAREN, TokenType.LBRACE, TokenType.RBRACE,
        TokenType.LBRACKET, TokenType.RBRACKET, TokenType.SEMICOLON, TokenType.COMMA,
        TokenType.COLON,
    ]
    assert [t.type for t in res.tokens[:-1]] == expected


# ── Comments & Preprocessor ───────────────────────────────────────────
def test_single_line_comment():
    src = "int x; // this is a comment\nint y;"
    res = tokenize(src)
    assert len(res.errors) == 0
    assert [t.lexeme for t in res.tokens[:-1]] == ["int", "x", ";", "int", "y", ";"]


def test_block_comment():
    src = "int /* comment inside */ x = /* another */ 5;"
    res = tokenize(src)
    assert len(res.errors) == 0
    assert [t.lexeme for t in res.tokens[:-1]] == ["int", "x", "=", "5", ";"]


def test_preprocessor_skipped():
    src = '#include <stdio.h>\n#define FOO 42\nint main() { return 0; }'
    res = tokenize(src)
    assert len(res.errors) == 0
    lexemes = [t.lexeme for t in res.tokens[:-1]]
    assert "include" not in lexemes
    assert "define" not in lexemes
    assert lexemes == ["int", "main", "(", ")", "{", "return", "0", ";", "}"]


# ── Line & Column Tracking ────────────────────────────────────────────
def test_line_and_col():
    src = "int x;\nx = 5;"
    res = tokenize(src)
    assert res.tokens[0] == Token(TokenType.KW_INT, "int", 1, 1)
    assert res.tokens[1] == Token(TokenType.IDENTIFIER, "x", 1, 5)
    assert res.tokens[2] == Token(TokenType.SEMICOLON, ";", 1, 6)
    assert res.tokens[3] == Token(TokenType.IDENTIFIER, "x", 2, 1)
    assert res.tokens[4] == Token(TokenType.ASSIGN, "=", 2, 3)
    assert res.tokens[5] == Token(TokenType.INT_LITERAL, "5", 2, 5)
    assert res.tokens[6] == Token(TokenType.SEMICOLON, ";", 2, 6)


# ── Error Cases (never crash, return Diagnostics) ────────────────────
def test_unterminated_block_comment():
    src = "int x; /* never closed"
    res = tokenize(src)
    assert len(res.errors) == 1
    assert res.errors[0].phase == "lexer"
    assert res.errors[0].severity == "error"
    assert "comment" in res.errors[0].message.lower()


def test_unterminated_string():
    src = 'int x; "hello'
    res = tokenize(src)
    assert len(res.errors) == 1
    assert res.errors[0].phase == "lexer"
    assert "string" in res.errors[0].message.lower()


def test_unterminated_char():
    src = "char c = 'a"
    res = tokenize(src)
    assert len(res.errors) == 1
    assert res.errors[0].phase == "lexer"


def test_unexpected_character():
    src = "int x = @ + $;"
    res = tokenize(src)
    assert len(res.errors) == 2
    for err in res.errors:
        assert err.phase == "lexer"
        assert err.severity == "error"


def test_scanf_ampersand():
    src = 'scanf("%d", &x);'
    res = tokenize(src)
    assert len(res.errors) == 0
    types = [t.type for t in res.tokens[:-1]]
    assert TokenType.AMP in types
