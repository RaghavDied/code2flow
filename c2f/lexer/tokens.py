"""Token definitions for the C-subset lexer (CONTRACTS section 4)."""

from dataclasses import dataclass
from enum import Enum


class TokenType(str, Enum):
    """All token kinds. Member name equals member value."""

    # Keywords
    KW_INT = "KW_INT"
    KW_FLOAT = "KW_FLOAT"
    KW_CHAR = "KW_CHAR"
    KW_VOID = "KW_VOID"
    KW_IF = "KW_IF"
    KW_ELSE = "KW_ELSE"
    KW_WHILE = "KW_WHILE"
    KW_DO = "KW_DO"
    KW_FOR = "KW_FOR"
    KW_SWITCH = "KW_SWITCH"
    KW_CASE = "KW_CASE"
    KW_DEFAULT = "KW_DEFAULT"
    KW_BREAK = "KW_BREAK"
    KW_CONTINUE = "KW_CONTINUE"
    KW_RETURN = "KW_RETURN"

    # Literals and names
    IDENTIFIER = "IDENTIFIER"
    INT_LITERAL = "INT_LITERAL"
    FLOAT_LITERAL = "FLOAT_LITERAL"
    CHAR_LITERAL = "CHAR_LITERAL"
    STRING_LITERAL = "STRING_LITERAL"

    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    PERCENT = "PERCENT"
    ASSIGN = "ASSIGN"
    PLUS_ASSIGN = "PLUS_ASSIGN"
    MINUS_ASSIGN = "MINUS_ASSIGN"
    STAR_ASSIGN = "STAR_ASSIGN"
    SLASH_ASSIGN = "SLASH_ASSIGN"
    INC = "INC"
    DEC = "DEC"
    EQ = "EQ"
    NE = "NE"
    LT = "LT"
    LE = "LE"
    GT = "GT"
    GE = "GE"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    AMP = "AMP"  # only so scanf("%d", &x) works

    # Punctuation
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    SEMICOLON = "SEMICOLON"
    COMMA = "COMMA"
    COLON = "COLON"

    # Special
    EOF = "EOF"


@dataclass
class Token:
    """One lexical token. line and col are 1-based."""

    type: TokenType
    lexeme: str
    line: int
    col: int


KEYWORDS: dict[str, TokenType] = {
    "int": TokenType.KW_INT,
    "float": TokenType.KW_FLOAT,
    "char": TokenType.KW_CHAR,
    "void": TokenType.KW_VOID,
    "if": TokenType.KW_IF,
    "else": TokenType.KW_ELSE,
    "while": TokenType.KW_WHILE,
    "do": TokenType.KW_DO,
    "for": TokenType.KW_FOR,
    "switch": TokenType.KW_SWITCH,
    "case": TokenType.KW_CASE,
    "default": TokenType.KW_DEFAULT,
    "break": TokenType.KW_BREAK,
    "continue": TokenType.KW_CONTINUE,
    "return": TokenType.KW_RETURN,
}
