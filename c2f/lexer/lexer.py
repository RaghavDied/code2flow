"""Hand-written lexer for the supported C subset. Owner: Kushan.

Lexer skips whitespace, ``//`` and ``/* */`` comments, and preprocessor
lines starting with ``#``.  It never raises on bad input; it records a
:class:`~c2f.common.Diagnostic` and continues.

Public API
----------
tokenize(source: str) -> LexResult
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from c2f.common import Diagnostic

from .tokens import Token, TokenType

# ── keyword map ───────────────────────────────────────────────────────
_KEYWORDS: dict[str, TokenType] = {
    "int":      TokenType.KW_INT,
    "float":    TokenType.KW_FLOAT,
    "char":     TokenType.KW_CHAR,
    "void":     TokenType.KW_VOID,
    "if":       TokenType.KW_IF,
    "else":     TokenType.KW_ELSE,
    "while":    TokenType.KW_WHILE,
    "do":       TokenType.KW_DO,
    "for":      TokenType.KW_FOR,
    "switch":   TokenType.KW_SWITCH,
    "case":     TokenType.KW_CASE,
    "default":  TokenType.KW_DEFAULT,
    "break":    TokenType.KW_BREAK,
    "continue": TokenType.KW_CONTINUE,
    "return":   TokenType.KW_RETURN,
}


@dataclass
class LexResult:
    """Result returned by :func:`tokenize`."""
    tokens: List[Token] = field(default_factory=list)
    errors: List[Diagnostic] = field(default_factory=list)


# ── lexer implementation ──────────────────────────────────────────────
class _Lexer:
    """Internal scanning state.  Instantiated once per ``tokenize`` call."""

    def __init__(self, source: str) -> None:
        self._src = source
        self._pos = 0
        self._line = 1
        self._col = 1
        self._tokens: list[Token] = []
        self._errors: list[Diagnostic] = []

    # ── helpers ───────────────────────────────────────────────────────
    def _peek(self, offset: int = 0) -> str:
        """Return char at current position + *offset*, or ``''`` at EOF."""
        idx = self._pos + offset
        return self._src[idx] if idx < len(self._src) else ""

    def _advance(self) -> str:
        """Consume and return the current char, updating line/col."""
        ch = self._src[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col = 1
        else:
            self._col += 1
        return ch

    def _at_end(self) -> bool:
        return self._pos >= len(self._src)

    def _add(self, tt: TokenType, lexeme: str, line: int, col: int) -> None:
        self._tokens.append(Token(tt, lexeme, line, col))

    def _error(self, msg: str, line: int, col: int) -> None:
        self._errors.append(Diagnostic("lexer", "error", msg, line, col))

    # ── whitespace & comments ─────────────────────────────────────────
    def _skip_whitespace_and_comments(self) -> None:
        while not self._at_end():
            ch = self._peek()
            # plain whitespace
            if ch in " \t\r\n":
                self._advance()
                continue
            # single-line comment
            if ch == "/" and self._peek(1) == "/":
                self._advance()  # /
                self._advance()  # /
                while not self._at_end() and self._peek() != "\n":
                    self._advance()
                continue
            # block comment
            if ch == "/" and self._peek(1) == "*":
                start_line, start_col = self._line, self._col
                self._advance()  # /
                self._advance()  # *
                while not self._at_end():
                    if self._peek() == "*" and self._peek(1) == "/":
                        self._advance()  # *
                        self._advance()  # /
                        break
                    self._advance()
                else:
                    self._error("Unterminated block comment", start_line, start_col)
                continue
            # preprocessor line (skip entire line starting with #)
            if ch == "#":
                while not self._at_end() and self._peek() != "\n":
                    self._advance()
                continue
            break

    # ── number literals ───────────────────────────────────────────────
    def _read_number(self) -> None:
        start_line, start_col = self._line, self._col
        lexeme = ""
        is_float = False

        while not self._at_end() and (self._peek().isdigit()):
            lexeme += self._advance()

        # decimal part
        if not self._at_end() and self._peek() == "." and self._peek(1).isdigit():
            is_float = True
            lexeme += self._advance()  # the dot
            while not self._at_end() and self._peek().isdigit():
                lexeme += self._advance()

        tt = TokenType.FLOAT_LITERAL if is_float else TokenType.INT_LITERAL
        self._add(tt, lexeme, start_line, start_col)

    # ── string literal ────────────────────────────────────────────────
    def _read_string(self) -> None:
        start_line, start_col = self._line, self._col
        self._advance()  # opening "
        lexeme = '"'
        while not self._at_end() and self._peek() != '"':
            if self._peek() == "\n":
                self._error("Unterminated string literal", start_line, start_col)
                self._add(TokenType.STRING_LITERAL, lexeme + '"', start_line, start_col)
                return
            if self._peek() == "\\":
                lexeme += self._advance()  # backslash
                if not self._at_end():
                    lexeme += self._advance()  # escaped char
            else:
                lexeme += self._advance()
        if self._at_end():
            self._error("Unterminated string literal", start_line, start_col)
            lexeme += '"'
        else:
            lexeme += self._advance()  # closing "
        self._add(TokenType.STRING_LITERAL, lexeme, start_line, start_col)

    # ── char literal ──────────────────────────────────────────────────
    def _read_char(self) -> None:
        start_line, start_col = self._line, self._col
        self._advance()  # opening '
        lexeme = "'"
        if self._at_end() or self._peek() == "\n":
            self._error("Unterminated char literal", start_line, start_col)
            self._add(TokenType.CHAR_LITERAL, lexeme + "'", start_line, start_col)
            return
        if self._peek() == "\\":
            lexeme += self._advance()
            if not self._at_end() and self._peek() != "\n":
                lexeme += self._advance()
        else:
            lexeme += self._advance()
        if not self._at_end() and self._peek() == "'":
            lexeme += self._advance()
        else:
            self._error("Unterminated char literal", start_line, start_col)
            lexeme += "'"
        self._add(TokenType.CHAR_LITERAL, lexeme, start_line, start_col)

    # ── identifier / keyword ──────────────────────────────────────────
    def _read_identifier(self) -> None:
        start_line, start_col = self._line, self._col
        lexeme = ""
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            lexeme += self._advance()
        tt = _KEYWORDS.get(lexeme, TokenType.IDENTIFIER)
        self._add(tt, lexeme, start_line, start_col)

    # ── main scan loop ────────────────────────────────────────────────
    def scan(self) -> LexResult:
        """Produce all tokens from the source."""
        while not self._at_end():
            self._skip_whitespace_and_comments()
            if self._at_end():
                break

            start_line, start_col = self._line, self._col
            ch = self._peek()

            # numbers
            if ch.isdigit():
                self._read_number()
                continue
            # identifiers / keywords
            if ch.isalpha() or ch == "_":
                self._read_identifier()
                continue
            # string literal
            if ch == '"':
                self._read_string()
                continue
            # char literal
            if ch == "'":
                self._read_char()
                continue

            # two-char operators (check before single-char)
            two = ch + self._peek(1) if not self._at_end() else ""
            if two == "++":
                self._advance(); self._advance()
                self._add(TokenType.INC, "++", start_line, start_col)
                continue
            if two == "--":
                self._advance(); self._advance()
                self._add(TokenType.DEC, "--", start_line, start_col)
                continue
            if two == "+=":
                self._advance(); self._advance()
                self._add(TokenType.PLUS_ASSIGN, "+=", start_line, start_col)
                continue
            if two == "-=":
                self._advance(); self._advance()
                self._add(TokenType.MINUS_ASSIGN, "-=", start_line, start_col)
                continue
            if two == "*=":
                self._advance(); self._advance()
                self._add(TokenType.STAR_ASSIGN, "*=", start_line, start_col)
                continue
            if two == "/=":
                self._advance(); self._advance()
                self._add(TokenType.SLASH_ASSIGN, "/=", start_line, start_col)
                continue
            if two == "==":
                self._advance(); self._advance()
                self._add(TokenType.EQ, "==", start_line, start_col)
                continue
            if two == "!=":
                self._advance(); self._advance()
                self._add(TokenType.NE, "!=", start_line, start_col)
                continue
            if two == "<=":
                self._advance(); self._advance()
                self._add(TokenType.LE, "<=", start_line, start_col)
                continue
            if two == ">=":
                self._advance(); self._advance()
                self._add(TokenType.GE, ">=", start_line, start_col)
                continue
            if two == "&&":
                self._advance(); self._advance()
                self._add(TokenType.AND, "&&", start_line, start_col)
                continue
            if two == "||":
                self._advance(); self._advance()
                self._add(TokenType.OR, "||", start_line, start_col)
                continue

            # single-char operators / punctuation
            self._advance()
            match ch:
                case "+": self._add(TokenType.PLUS, "+", start_line, start_col)
                case "-": self._add(TokenType.MINUS, "-", start_line, start_col)
                case "*": self._add(TokenType.STAR, "*", start_line, start_col)
                case "/": self._add(TokenType.SLASH, "/", start_line, start_col)
                case "%": self._add(TokenType.PERCENT, "%", start_line, start_col)
                case "=": self._add(TokenType.ASSIGN, "=", start_line, start_col)
                case "<": self._add(TokenType.LT, "<", start_line, start_col)
                case ">": self._add(TokenType.GT, ">", start_line, start_col)
                case "!": self._add(TokenType.NOT, "!", start_line, start_col)
                case "&": self._add(TokenType.AMP, "&", start_line, start_col)
                case "(": self._add(TokenType.LPAREN, "(", start_line, start_col)
                case ")": self._add(TokenType.RPAREN, ")", start_line, start_col)
                case "{": self._add(TokenType.LBRACE, "{", start_line, start_col)
                case "}": self._add(TokenType.RBRACE, "}", start_line, start_col)
                case "[": self._add(TokenType.LBRACKET, "[", start_line, start_col)
                case "]": self._add(TokenType.RBRACKET, "]", start_line, start_col)
                case ";": self._add(TokenType.SEMICOLON, ";", start_line, start_col)
                case ",": self._add(TokenType.COMMA, ",", start_line, start_col)
                case ":": self._add(TokenType.COLON, ":", start_line, start_col)
                case _:
                    self._error(
                        f"Unexpected character {ch!r}", start_line, start_col
                    )

        # always end with EOF
        self._add(TokenType.EOF, "", self._line, self._col)
        return LexResult(tokens=self._tokens, errors=self._errors)


def tokenize(source: str) -> LexResult:
    """Tokenize *source* into a list of tokens.

    Never raises on bad input; records a :class:`~c2f.common.Diagnostic`
    and continues.
    """
    return _Lexer(source).scan()
