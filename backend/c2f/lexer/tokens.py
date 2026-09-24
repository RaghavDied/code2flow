"""Token types (CONTRACTS.md section 4). Owner: Kushan.
# SKELETON STUB created by Raghav. The owner replaces this file; keep the public names/signatures from CONTRACTS.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenType(str, Enum):
    """Member name == value."""

    # Keywords
    KW_INT = "KW_INT"; KW_FLOAT = "KW_FLOAT"; KW_CHAR = "KW_CHAR"; KW_VOID = "KW_VOID"
    KW_IF = "KW_IF"; KW_ELSE = "KW_ELSE"; KW_WHILE = "KW_WHILE"; KW_DO = "KW_DO"
    KW_FOR = "KW_FOR"; KW_SWITCH = "KW_SWITCH"; KW_CASE = "KW_CASE"; KW_DEFAULT = "KW_DEFAULT"
    KW_BREAK = "KW_BREAK"; KW_CONTINUE = "KW_CONTINUE"; KW_RETURN = "KW_RETURN"
    # Literals / names
    IDENTIFIER = "IDENTIFIER"; INT_LITERAL = "INT_LITERAL"; FLOAT_LITERAL = "FLOAT_LITERAL"
    CHAR_LITERAL = "CHAR_LITERAL"; STRING_LITERAL = "STRING_LITERAL"
    # Operators
    PLUS = "PLUS"; MINUS = "MINUS"; STAR = "STAR"; SLASH = "SLASH"; PERCENT = "PERCENT"
    ASSIGN = "ASSIGN"; PLUS_ASSIGN = "PLUS_ASSIGN"; MINUS_ASSIGN = "MINUS_ASSIGN"
    STAR_ASSIGN = "STAR_ASSIGN"; SLASH_ASSIGN = "SLASH_ASSIGN"; INC = "INC"; DEC = "DEC"
    EQ = "EQ"; NE = "NE"; LT = "LT"; LE = "LE"; GT = "GT"; GE = "GE"
    AND = "AND"; OR = "OR"; NOT = "NOT"; AMP = "AMP"
    # Punctuation
    LPAREN = "LPAREN"; RPAREN = "RPAREN"; LBRACE = "LBRACE"; RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"; RBRACKET = "RBRACKET"; SEMICOLON = "SEMICOLON"
    COMMA = "COMMA"; COLON = "COLON"
    # Special
    EOF = "EOF"


@dataclass
class Token:
    """line and col are 1-based."""

    type: TokenType
    lexeme: str
    line: int
    col: int
