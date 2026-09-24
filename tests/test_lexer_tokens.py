"""Tests for c2f.lexer.tokens (imports the module directly: Kushan's own internals)."""

from c2f.lexer.tokens import KEYWORDS, Token, TokenType

EXPECTED = (
    "KW_INT KW_FLOAT KW_CHAR KW_VOID KW_IF KW_ELSE KW_WHILE KW_DO KW_FOR KW_SWITCH "
    "KW_CASE KW_DEFAULT KW_BREAK KW_CONTINUE KW_RETURN "
    "IDENTIFIER INT_LITERAL FLOAT_LITERAL CHAR_LITERAL STRING_LITERAL "
    "PLUS MINUS STAR SLASH PERCENT ASSIGN PLUS_ASSIGN MINUS_ASSIGN STAR_ASSIGN "
    "SLASH_ASSIGN INC DEC EQ NE LT LE GT GE AND OR NOT AMP "
    "LPAREN RPAREN LBRACE RBRACE LBRACKET RBRACKET SEMICOLON COMMA COLON "
    "EOF"
).split()


def test_token_type_members_match_contract():
    assert [t.name for t in TokenType] == EXPECTED
    assert len(EXPECTED) == 52


def test_member_name_equals_value():
    for t in TokenType:
        assert t.name == t.value


def test_keywords_map_to_kw_types():
    assert len(KEYWORDS) == 15
    for word, tt in KEYWORDS.items():
        assert tt.name == "KW_" + word.upper()


def test_token_fields():
    tok = Token(TokenType.IDENTIFIER, "x", 3, 5)
    assert (tok.type, tok.lexeme, tok.line, tok.col) == (TokenType.IDENTIFIER, "x", 3, 5)
