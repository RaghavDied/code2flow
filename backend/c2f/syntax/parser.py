"""Recursive-descent parser with precedence climbing for expressions.

Owner: Kushan.

Supports the full C subset from CONTRACTS.md section 5.  Panic-mode
error recovery at ``;`` and ``}``.

Integration Contract with Raghav (Semantic Checker & Diagnostics)
-----------------------------------------------------------------
1. Diagnostic Format (diagnostics.py):
   Kushan uses Raghav's Diagnostic dataclass to report syntax errors with
   1-based line and col so errors display uniformly across the whole application.

2. AST Validation:
   Kushan's AST node dataclasses are validated and annotated by Raghav's semantic
   checker (analyze).

Public API
----------
parse(tokens: list[Token]) -> ParseResult
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from c2f.common import Diagnostic
from c2f.lexer import Token, TokenType

from .ast_nodes import (
    Assign,
    ArrayAccess,
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
    Node,
    Param,
    Program,
    Return,
    Switch,
    UnaryOp,
    VarDecl,
    While,
)


@dataclass
class ParseResult:
    """Result of :func:`parse`."""
    ast: Optional[Program] = None
    errors: List[Diagnostic] = field(default_factory=list)


# ── precedence table (precedence climbing) ────────────────────────────
# higher number = tighter binding
_BINARY_PREC: dict[TokenType, int] = {
    TokenType.OR:      1,
    TokenType.AND:     2,
    TokenType.EQ:      3,
    TokenType.NE:      3,
    TokenType.LT:      4,
    TokenType.LE:      4,
    TokenType.GT:      4,
    TokenType.GE:      4,
    TokenType.PLUS:    5,
    TokenType.MINUS:   5,
    TokenType.STAR:    6,
    TokenType.SLASH:   6,
    TokenType.PERCENT: 6,
}

_OP_LEXEME: dict[TokenType, str] = {
    TokenType.OR:      "||",
    TokenType.AND:     "&&",
    TokenType.EQ:      "==",
    TokenType.NE:      "!=",
    TokenType.LT:      "<",
    TokenType.LE:      "<=",
    TokenType.GT:      ">",
    TokenType.GE:      ">=",
    TokenType.PLUS:    "+",
    TokenType.MINUS:   "-",
    TokenType.STAR:    "*",
    TokenType.SLASH:   "/",
    TokenType.PERCENT: "%",
}

_TYPE_KEYWORDS = {TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_CHAR, TokenType.KW_VOID}
_TYPE_MAP: dict[TokenType, str] = {
    TokenType.KW_INT:   "int",
    TokenType.KW_FLOAT: "float",
    TokenType.KW_CHAR:  "char",
    TokenType.KW_VOID:  "void",
}

_ASSIGN_OPS = {
    TokenType.ASSIGN,
    TokenType.PLUS_ASSIGN,
    TokenType.MINUS_ASSIGN,
    TokenType.STAR_ASSIGN,
    TokenType.SLASH_ASSIGN,
}
_ASSIGN_LEXEME: dict[TokenType, str] = {
    TokenType.ASSIGN:       "=",
    TokenType.PLUS_ASSIGN:  "+=",
    TokenType.MINUS_ASSIGN: "-=",
    TokenType.STAR_ASSIGN:  "*=",
    TokenType.SLASH_ASSIGN: "/=",
}


# ── parser implementation ─────────────────────────────────────────────
class _Parser:
    """Internal parser state.  One instance per :func:`parse` call."""

    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._pos = 0
        self._errors: list[Diagnostic] = []

    # ── helpers ───────────────────────────────────────────────────────
    def _cur(self) -> Token:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        # Defensive: should never happen if lexer emits EOF
        last = self._tokens[-1] if self._tokens else Token(TokenType.EOF, "", 1, 1)
        return Token(TokenType.EOF, "", last.line, last.col)

    def _peek(self, offset: int = 0) -> Token:
        idx = self._pos + offset
        if idx < len(self._tokens):
            return self._tokens[idx]
        last = self._tokens[-1] if self._tokens else Token(TokenType.EOF, "", 1, 1)
        return Token(TokenType.EOF, "", last.line, last.col)

    def _at_end(self) -> bool:
        return self._cur().type == TokenType.EOF

    def _check(self, tt: TokenType) -> bool:
        return self._cur().type == tt

    def _match(self, *types: TokenType) -> Optional[Token]:
        if self._cur().type in types:
            tok = self._cur()
            self._pos += 1
            return tok
        return None

    def _expect(self, tt: TokenType, msg: str) -> Optional[Token]:
        tok = self._match(tt)
        if tok is None:
            cur = self._cur()
            self._error(msg, cur.line, cur.col)
        return tok

    def _error(self, msg: str, line: int, col: int) -> None:
        self._errors.append(Diagnostic("parser", "error", msg, line, col))

    # ── panic-mode recovery ───────────────────────────────────────────
    def _synchronize(self) -> None:
        """Advance until we find a safe re-synchronisation point."""
        # Always consume at least one token to guarantee progress
        if not self._at_end():
            self._pos += 1
        while not self._at_end():
            if self._cur().type == TokenType.SEMICOLON:
                self._pos += 1  # consume the ;
                return
            if self._cur().type == TokenType.RBRACE:
                return  # don't consume; the block loop needs it
            if self._cur().type in (
                TokenType.KW_IF, TokenType.KW_WHILE, TokenType.KW_DO,
                TokenType.KW_FOR, TokenType.KW_SWITCH, TokenType.KW_RETURN,
                TokenType.KW_BREAK, TokenType.KW_CONTINUE,
            ):
                return
            if self._cur().type in _TYPE_KEYWORDS:
                return
            self._pos += 1

    # ── top-level ─────────────────────────────────────────────────────
    def parse_program(self) -> Program:
        """program -> function*"""
        tok = self._cur()
        functions: list[Function] = []
        while not self._at_end():
            fn = self._parse_function()
            if fn is not None:
                functions.append(fn)
        return Program(line=tok.line, col=tok.col, functions=functions)

    def _parse_function(self) -> Optional[Function]:
        """function -> type ID '(' params ')' block"""
        tok = self._cur()
        # return type
        type_tok = self._match(*_TYPE_KEYWORDS)
        if type_tok is None:
            self._error(
                f"Expected type keyword (int/float/char/void), got {self._cur().lexeme!r}",
                tok.line, tok.col,
            )
            self._synchronize()
            return None

        ret_type = _TYPE_MAP[type_tok.type]

        # function name
        name_tok = self._expect(TokenType.IDENTIFIER, "Expected function name")
        if name_tok is None:
            self._synchronize()
            return None
        name = name_tok.lexeme

        # params
        if self._expect(TokenType.LPAREN, "Expected '(' after function name") is None:
            self._synchronize()
            return None
        params = self._parse_params()
        if self._expect(TokenType.RPAREN, "Expected ')' after parameters") is None:
            self._synchronize()
            return None

        # body
        body = self._parse_block()
        if body is None:
            return None
        return Function(
            line=tok.line, col=tok.col,
            name=name, return_type=ret_type, params=params, body=body,
        )

    def _parse_params(self) -> list[Param]:
        """params -> (type ID (',' type ID)*)?"""
        params: list[Param] = []
        if self._cur().type == TokenType.RPAREN:
            return params
        while True:
            type_tok = self._match(*_TYPE_KEYWORDS)
            if type_tok is None:
                self._error("Expected parameter type", self._cur().line, self._cur().col)
                break
            name_tok = self._expect(TokenType.IDENTIFIER, "Expected parameter name")
            if name_tok is None:
                break
            params.append(Param(type=_TYPE_MAP[type_tok.type], name=name_tok.lexeme))
            if not self._match(TokenType.COMMA):
                break
        return params

    # ── block ─────────────────────────────────────────────────────────
    def _parse_block(self) -> Optional[Block]:
        """block -> '{' statement* '}'"""
        tok = self._cur()
        if self._expect(TokenType.LBRACE, "Expected '{'") is None:
            self._synchronize()
            return None
        stmts: list[Node] = []
        while not self._at_end() and not self._check(TokenType.RBRACE):
            pos_before = self._pos
            stmt = self._parse_statement()
            if stmt is not None:
                stmts.append(stmt)
            elif self._pos == pos_before:
                # Guarantee forward progress on error
                self._pos += 1
        if self._expect(TokenType.RBRACE, "Expected '}'") is None:
            pass  # already recorded error; continue
        return Block(line=tok.line, col=tok.col, statements=stmts)

    # ── statements ────────────────────────────────────────────────────
    def _parse_statement(self) -> Optional[Node]:
        """Dispatch to the appropriate statement parser."""
        tok = self._cur()
        tt = tok.type

        if tt in _TYPE_KEYWORDS:
            return self._parse_declaration()
        if tt == TokenType.KW_IF:
            return self._parse_if()
        if tt == TokenType.KW_WHILE:
            return self._parse_while()
        if tt == TokenType.KW_DO:
            return self._parse_do_while()
        if tt == TokenType.KW_FOR:
            return self._parse_for()
        if tt == TokenType.KW_SWITCH:
            return self._parse_switch()
        if tt == TokenType.KW_RETURN:
            return self._parse_return()
        if tt == TokenType.KW_BREAK:
            self._pos += 1
            self._expect(TokenType.SEMICOLON, "Expected ';' after 'break'")
            return Break(line=tok.line, col=tok.col)
        if tt == TokenType.KW_CONTINUE:
            self._pos += 1
            self._expect(TokenType.SEMICOLON, "Expected ';' after 'continue'")
            return Continue(line=tok.line, col=tok.col)
        if tt == TokenType.LBRACE:
            return self._parse_block()

        # expression statement (assignment, call, increment …)
        return self._parse_expr_statement()

    # ── declarations ──────────────────────────────────────────────────
    def _parse_declaration(self) -> Optional[VarDecl]:
        """declaration -> type ID ('[' INT ']')? ('=' expr)? ';'"""
        tok = self._cur()
        type_tok = self._match(*_TYPE_KEYWORDS)
        if type_tok is None:
            self._error("Expected type", tok.line, tok.col)
            self._synchronize()
            return None
        var_type = _TYPE_MAP[type_tok.type]

        name_tok = self._expect(TokenType.IDENTIFIER, "Expected variable name")
        if name_tok is None:
            self._synchronize()
            return None
        name = name_tok.lexeme

        # optional array size
        array_size: Optional[int] = None
        if self._match(TokenType.LBRACKET):
            size_tok = self._expect(TokenType.INT_LITERAL, "Expected array size")
            if size_tok is not None:
                array_size = int(size_tok.lexeme)
            self._expect(TokenType.RBRACKET, "Expected ']'")

        # optional initialiser
        init: Optional[Node] = None
        if self._match(TokenType.ASSIGN):
            init = self._parse_expression()

        self._expect(TokenType.SEMICOLON, "Expected ';' after declaration")
        return VarDecl(
            line=tok.line, col=tok.col,
            var_type=var_type, name=name, array_size=array_size, init=init,
        )

    # ── if ────────────────────────────────────────────────────────────
    def _parse_if(self) -> Optional[If]:
        tok = self._cur()
        self._pos += 1  # consume 'if'
        if self._expect(TokenType.LPAREN, "Expected '(' after 'if'") is None:
            self._synchronize()
            return None
        cond = self._parse_expression()
        if self._expect(TokenType.RPAREN, "Expected ')' after if condition") is None:
            self._synchronize()
            return None
        then_stmt = self._parse_statement()
        else_stmt: Optional[Node] = None
        if self._match(TokenType.KW_ELSE):
            else_stmt = self._parse_statement()
        return If(line=tok.line, col=tok.col, cond=cond, then=then_stmt, else_=else_stmt)

    # ── while ─────────────────────────────────────────────────────────
    def _parse_while(self) -> Optional[While]:
        tok = self._cur()
        self._pos += 1  # consume 'while'
        if self._expect(TokenType.LPAREN, "Expected '(' after 'while'") is None:
            self._synchronize()
            return None
        cond = self._parse_expression()
        if self._expect(TokenType.RPAREN, "Expected ')' after while condition") is None:
            self._synchronize()
            return None
        body = self._parse_statement()
        return While(line=tok.line, col=tok.col, cond=cond, body=body)

    # ── do-while ──────────────────────────────────────────────────────
    def _parse_do_while(self) -> Optional[DoWhile]:
        tok = self._cur()
        self._pos += 1  # consume 'do'
        body = self._parse_statement()
        if self._expect(TokenType.KW_WHILE, "Expected 'while' after do body") is None:
            self._synchronize()
            return None
        if self._expect(TokenType.LPAREN, "Expected '(' after 'while'") is None:
            self._synchronize()
            return None
        cond = self._parse_expression()
        if self._expect(TokenType.RPAREN, "Expected ')' after do-while condition") is None:
            self._synchronize()
            return None
        self._expect(TokenType.SEMICOLON, "Expected ';' after do-while")
        return DoWhile(line=tok.line, col=tok.col, body=body, cond=cond)

    # ── for ───────────────────────────────────────────────────────────
    def _parse_for(self) -> Optional[For]:
        tok = self._cur()
        self._pos += 1  # consume 'for'
        if self._expect(TokenType.LPAREN, "Expected '(' after 'for'") is None:
            self._synchronize()
            return None

        # init: declaration or expression-statement or empty
        init: Optional[Node] = None
        if self._cur().type in _TYPE_KEYWORDS:
            init = self._parse_declaration()
            # declaration already consumed the ';'
        elif not self._check(TokenType.SEMICOLON):
            init = self._parse_expression_or_assign()
            self._expect(TokenType.SEMICOLON, "Expected ';' in for-init")
        else:
            self._pos += 1  # consume empty ';'

        # condition
        cond: Optional[Node] = None
        if not self._check(TokenType.SEMICOLON):
            cond = self._parse_expression()
        self._expect(TokenType.SEMICOLON, "Expected ';' after for-condition")

        # update
        update: Optional[Node] = None
        if not self._check(TokenType.RPAREN):
            update = self._parse_expression_or_assign()

        if self._expect(TokenType.RPAREN, "Expected ')' after for clauses") is None:
            self._synchronize()
            return None
        body = self._parse_statement()
        return For(line=tok.line, col=tok.col, init=init, cond=cond, update=update, body=body)

    # ── switch ────────────────────────────────────────────────────────
    def _parse_switch(self) -> Optional[Switch]:
        tok = self._cur()
        self._pos += 1  # consume 'switch'
        if self._expect(TokenType.LPAREN, "Expected '(' after 'switch'") is None:
            self._synchronize()
            return None
        expr = self._parse_expression()
        if self._expect(TokenType.RPAREN, "Expected ')' after switch expression") is None:
            self._synchronize()
            return None
        if self._expect(TokenType.LBRACE, "Expected '{' before switch cases") is None:
            self._synchronize()
            return None

        cases: list[Case] = []
        while not self._at_end() and not self._check(TokenType.RBRACE):
            c = self._parse_case()
            if c is not None:
                cases.append(c)

        self._expect(TokenType.RBRACE, "Expected '}' after switch body")
        return Switch(line=tok.line, col=tok.col, expr=expr, cases=cases)

    def _parse_case(self) -> Optional[Case]:
        tok = self._cur()
        value: Optional[Node] = None
        if self._match(TokenType.KW_CASE):
            value = self._parse_expression()
            self._expect(TokenType.COLON, "Expected ':' after case value")
        elif self._match(TokenType.KW_DEFAULT):
            self._expect(TokenType.COLON, "Expected ':' after 'default'")
        else:
            self._error("Expected 'case' or 'default'", tok.line, tok.col)
            self._synchronize()
            return None

        body: list[Node] = []
        while (
            not self._at_end()
            and not self._check(TokenType.KW_CASE)
            and not self._check(TokenType.KW_DEFAULT)
            and not self._check(TokenType.RBRACE)
        ):
            stmt = self._parse_statement()
            if stmt is not None:
                body.append(stmt)
        return Case(line=tok.line, col=tok.col, value=value, body=body)

    # ── return ────────────────────────────────────────────────────────
    def _parse_return(self) -> Optional[Return]:
        tok = self._cur()
        self._pos += 1  # consume 'return'
        value: Optional[Node] = None
        if not self._check(TokenType.SEMICOLON):
            value = self._parse_expression()
        self._expect(TokenType.SEMICOLON, "Expected ';' after return")
        return Return(line=tok.line, col=tok.col, value=value)

    # ── expression statement ──────────────────────────────────────────
    def _parse_expr_statement(self) -> Optional[Node]:
        """Parse an expression-statement (assignment, call, ++/-- …)."""
        tok = self._cur()
        node = self._parse_expression_or_assign()
        if node is None:
            self._error(f"Unexpected token {tok.lexeme!r}", tok.line, tok.col)
            self._synchronize()
            return None
        self._expect(TokenType.SEMICOLON, "Expected ';' after expression")
        # Wrap all top-level expressions (including assignments) in ExprStmt
        return ExprStmt(line=tok.line, col=tok.col, expr=node)

    # ── expression helpers ────────────────────────────────────────────
    def _parse_expression_or_assign(self) -> Optional[Node]:
        """Parse an expression; if followed by an assignment op, wrap in Assign."""
        expr = self._parse_expression()
        if expr is None:
            return None

        if self._cur().type in _ASSIGN_OPS:
            op_tok = self._cur()
            self._pos += 1
            rhs = self._parse_expression()
            return Assign(
                line=expr.line, col=expr.col,
                target=expr,
                op=_ASSIGN_LEXEME[op_tok.type],
                value=rhs,
            )
        return expr

    # ── precedence climbing expression parser ─────────────────────────
    def _parse_expression(self) -> Optional[Node]:
        """Parse an expression using precedence climbing."""
        return self._parse_prec(0)

    def _parse_prec(self, min_prec: int) -> Optional[Node]:
        """Parse a binary expression with minimum precedence *min_prec*."""
        left = self._parse_unary()
        if left is None:
            return None

        while True:
            tok = self._cur()
            prec = _BINARY_PREC.get(tok.type)
            if prec is None or prec < min_prec:
                break
            op_str = _OP_LEXEME[tok.type]
            self._pos += 1
            # left-associative: next level is prec + 1
            right = self._parse_prec(prec + 1)
            left = BinaryOp(
                line=left.line, col=left.col,
                op=op_str, left=left, right=right,
            )
        return left

    # ── unary ─────────────────────────────────────────────────────────
    def _parse_unary(self) -> Optional[Node]:
        tok = self._cur()

        # prefix ++ / --
        if tok.type == TokenType.INC:
            self._pos += 1
            operand = self._parse_unary()
            return UnaryOp(line=tok.line, col=tok.col, op="++", operand=operand, postfix=False)
        if tok.type == TokenType.DEC:
            self._pos += 1
            operand = self._parse_unary()
            return UnaryOp(line=tok.line, col=tok.col, op="--", operand=operand, postfix=False)
        # unary - and !
        if tok.type == TokenType.MINUS:
            self._pos += 1
            operand = self._parse_unary()
            return UnaryOp(line=tok.line, col=tok.col, op="-", operand=operand, postfix=False)
        if tok.type == TokenType.NOT:
            self._pos += 1
            operand = self._parse_unary()
            return UnaryOp(line=tok.line, col=tok.col, op="!", operand=operand, postfix=False)
        # address-of &
        if tok.type == TokenType.AMP:
            self._pos += 1
            operand = self._parse_unary()
            return UnaryOp(line=tok.line, col=tok.col, op="&", operand=operand, postfix=False)

        return self._parse_postfix()

    # ── postfix ───────────────────────────────────────────────────────
    def _parse_postfix(self) -> Optional[Node]:
        node = self._parse_primary()
        if node is None:
            return None

        while True:
            tok = self._cur()
            # postfix ++
            if tok.type == TokenType.INC:
                self._pos += 1
                node = UnaryOp(line=tok.line, col=tok.col, op="++", operand=node, postfix=True)
                continue
            # postfix --
            if tok.type == TokenType.DEC:
                self._pos += 1
                node = UnaryOp(line=tok.line, col=tok.col, op="--", operand=node, postfix=True)
                continue
            # array access  name[index]
            if tok.type == TokenType.LBRACKET and isinstance(node, Identifier):
                self._pos += 1  # consume [
                index = self._parse_expression()
                self._expect(TokenType.RBRACKET, "Expected ']'")
                node = ArrayAccess(
                    line=node.line, col=node.col,
                    name=node.name, index=index,
                )
                continue
            break
        return node

    # ── primary ───────────────────────────────────────────────────────
    def _parse_primary(self) -> Optional[Node]:
        tok = self._cur()

        # integer literal
        if tok.type == TokenType.INT_LITERAL:
            self._pos += 1
            return Literal(line=tok.line, col=tok.col, value=tok.lexeme, literal_type="int")
        # float literal
        if tok.type == TokenType.FLOAT_LITERAL:
            self._pos += 1
            return Literal(line=tok.line, col=tok.col, value=tok.lexeme, literal_type="float")
        # char literal
        if tok.type == TokenType.CHAR_LITERAL:
            self._pos += 1
            return Literal(line=tok.line, col=tok.col, value=tok.lexeme, literal_type="char")
        # string literal
        if tok.type == TokenType.STRING_LITERAL:
            self._pos += 1
            return Literal(line=tok.line, col=tok.col, value=tok.lexeme, literal_type="string")

        # identifier or function call
        if tok.type == TokenType.IDENTIFIER:
            self._pos += 1
            # function call?
            if self._check(TokenType.LPAREN):
                return self._parse_call(tok)
            return Identifier(line=tok.line, col=tok.col, name=tok.lexeme)

        # parenthesised expression
        if tok.type == TokenType.LPAREN:
            self._pos += 1
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN, "Expected ')'")
            return expr

        # nothing matched
        self._error(f"Expected expression, got {tok.lexeme!r}", tok.line, tok.col)
        self._synchronize()
        return None

    def _parse_call(self, name_tok: Token) -> Call:
        """Parse a function call after the name has been consumed."""
        self._pos += 1  # consume '('
        args: list[Node] = []
        if not self._check(TokenType.RPAREN):
            while True:
                arg = self._parse_expression()
                if arg is not None:
                    args.append(arg)
                if not self._match(TokenType.COMMA):
                    break
        self._expect(TokenType.RPAREN, "Expected ')' after arguments")
        return Call(line=name_tok.line, col=name_tok.col, name=name_tok.lexeme, args=args)


# ── public API ────────────────────────────────────────────────────────
def parse(tokens: List[Token]) -> ParseResult:
    """Parse *tokens* into an AST.

    Returns a :class:`ParseResult` with the AST (or ``None`` on fatal
    errors) and a list of diagnostics.
    """
    parser = _Parser(tokens)
    program = parser.parse_program()
    return ParseResult(ast=program, errors=parser._errors)
