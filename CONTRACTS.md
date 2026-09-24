# CONTRACTS

The single source of truth for names, formats and signatures. If the project doc and this file
disagree on names, folders or formats, THIS FILE WINS. Changes need a PR that names all four
teammates, and are announced in the group chat BEFORE coding them.

Positions: line and col are always 1-based.

## Clarifications added at repo creation (need a thumbs-up from the owners named)

1. (Kushan) Literal `value` in the AST and STRING_LITERAL / CHAR_LITERAL lexemes hold the source
   text INCLUDING quotes (`"%d"`, `'a'`), the same form TAC operands use.
2. (Ishani) When the optimiser rewrites an instruction it also rewrites that instruction's `src`
   so optimised flowchart labels show the new text (e.g. `printf("%d", 10)`, not `printf("%d", b)`).
3. (Ishani) A removed instruction's LogEntry uses `after = "(removed)"`.
4. (Raghav) `TacProgram.from_dict` and the API's `data.tac` carry no function params.

---

## 4. TOKEN CONTRACT (lexer -> parser)   [Kushan defines]

```
Token = dataclass(type: TokenType, lexeme: str, line: int, col: int)   # 1-based
TokenType (enum, member name = value):
  Keywords: KW_INT KW_FLOAT KW_CHAR KW_VOID KW_IF KW_ELSE KW_WHILE KW_DO KW_FOR KW_SWITCH
            KW_CASE KW_DEFAULT KW_BREAK KW_CONTINUE KW_RETURN
  Literals/names: IDENTIFIER INT_LITERAL FLOAT_LITERAL CHAR_LITERAL STRING_LITERAL
  Operators: PLUS MINUS STAR SLASH PERCENT ASSIGN PLUS_ASSIGN MINUS_ASSIGN STAR_ASSIGN
             SLASH_ASSIGN INC DEC EQ NE LT LE GT GE AND OR NOT AMP
  Punctuation: LPAREN RPAREN LBRACE RBRACE LBRACKET RBRACKET SEMICOLON COMMA COLON
  Special: EOF
```

Lexer skips whitespace, `//` and `/* */` comments, and preprocessor lines starting with `#`.

```
tokenize(source: str) -> LexResult(tokens: list[Token], errors: list[Diagnostic])
```

The lexer never raises on bad input; it records a Diagnostic and continues.
AMP exists only so `scanf("%d", &x)` works; `&` is otherwise unsupported.

## 5. AST CONTRACT (parser -> semantic/IR)   [Kushan defines]

```
parse(tokens: list[Token]) -> ParseResult(ast: Program | None, errors: list[Diagnostic])
```

Every node is a dataclass with `line: int` and `col: int`. `ast_to_dict(node)` produces JSON where
every object has "type", "line", "col" plus the fields below. Operators are source strings
("+", "==", "&&", "!", "++" ...). Absent optional children are null. Lists are [].

```
Program{functions:[Function]}
Function{name, return_type("int"|"float"|"char"|"void"), params:[{type,name}], body:Block}
Block{statements:[Stmt]}
VarDecl{var_type, name, array_size:int|null, init:Expr|null}
ExprStmt{expr:Expr}
If{cond:Expr, then:Stmt, else:Stmt|null}
While{cond:Expr, body:Stmt}
DoWhile{body:Stmt, cond:Expr}
For{init:Stmt|null, cond:Expr|null, update:Expr|null, body:Stmt}
Switch{expr:Expr, cases:[Case]}
Case{value:Expr|null (null = default), body:[Stmt]}
Return{value:Expr|null}
Break{}   Continue{}
Assign{target:Identifier|ArrayAccess, op:"="|"+="|"-="|"*="|"/=", value:Expr}
BinaryOp{op, left:Expr, right:Expr}
UnaryOp{op:"-"|"!"|"++"|"--"|"&", operand:Expr, postfix:bool}
Literal{value:str, literal_type:"int"|"float"|"char"|"string"}
Identifier{name}
ArrayAccess{name, index:Expr}
Call{name, args:[Expr]}
```

The semantic pass (Raghav) annotates expression nodes with a Python attribute `.expr_type`
("int"|"float"|"char"|"void"|"string"). This attribute is NOT part of the AST JSON.

## 6. TAC CONTRACT (IR -> optimiser -> CFG)   [Raghav defines with Ishani]

```
TacInstr = dataclass:
  id: int                 unique within the program. The optimiser NEVER renumbers ids of
                          instructions it keeps; new instructions get fresh ids (max id + 1).
  op: str                 one of the ops below
  result: str | None
  arg1: str | None
  arg2: str | None
  operator: str | None    only for binop / unop
  target: str | None      label name, only for goto / if_false / if_true
  label: str | None       only for op == "label"
  args: list[str]         only for call
  line: int               source line (1-based)
  src: str                original source text of the statement/condition, used for flowchart labels
TacFunction = dataclass(name: str, params: list[str], instrs: list[TacInstr])
TacProgram  = dataclass(functions: dict[str, TacFunction])   # key = function name, source order
```

Operands are strings. Temporaries match `^t[0-9]+$` (t1, t2 ... per function). Variables are their
source names. Literals are their source text (`"5"`, `"3.5"`, `"'a'"`, `"\"hi\""`). `is_literal(x)` in
`ir/tac.py` tells them apart. Labels are L0, L1, ... per function.

```
Ops and meaning:
  assign        result = arg1
  binop         result = arg1 <operator> arg2      operator in + - * / % < <= > >= == != && ||
  unop          result = <operator> arg1           operator in - !
  label         label: (defines label `label`)
  goto          goto target
  if_false      if !arg1 goto target
  if_true       if arg1 goto target
  call          [result =] call arg1(args...)      arg1 = function name (printf, scanf, user fn)
  return        return [arg1]
  array_load    result = arg1[arg2]
  array_store   arg1[arg2] = result                (yes, `result` holds the stored value operand)
```

Increment/decrement, compound assignment, for/do-while/switch are lowered to these ops by the
TAC generator. switch is lowered to `binop ==` + `if_true` chains, so fall-through works naturally.
break/continue become goto. Every function ends with an explicit `return`.
Each instruction is serialised to JSON with all the fields above (null / [] when unused).

```
Optimiser API:
  optimize(prog: TacProgram) -> OptimizeResult(program: TacProgram, log: list[LogEntry])
  LogEntry = dataclass(pass_name: str, function: str, line: int, instr_id: int,
                       action: "replaced"|"removed"|"added"|"moved", before: str, after: str)
  `before`/`after` are human-readable one-line strings like "t1 = 2 * 3" and "t1 = 6".
  optimize() must not mutate its input (deep-copy first).
  interpret(prog: TacProgram, inputs: list[str]) -> list[str]   # captured printf output lines
  tac_to_c(prog: TacProgram) -> str
```

Pass names (`LogEntry.pass_name`) are exactly: constant_folding, constant_propagation,
algebraic_simplification, dead_code_elimination, unreachable_code_removal, branch_simplification,
strength_reduction, copy_propagation, common_subexpression_elimination, loop_invariant_code_motion.

Every pass has the signature `def run(fn: TacFunction) -> list[LogEntry]` (mutates fn in place,
returns the log entries it produced; empty list means no change).

## 7. CFG CONTRACT (CFG builder -> API -> UI)   [Raghav defines with Sneh]

`build_cfg(fn: TacFunction) -> Cfg;  cfg_to_dict(cfg) -> dict`. JSON shape for one function:

```json
{
  "function": "main",
  "nodes": [
    { "id": "B0", "type": "start|end|process|decision|io",
      "label": "text shown in the box (multiple statements joined by \n; decisions end with ?)",
      "lines": [3, 4],
      "instr_ids": [1, 2, 3],
      "is_loop_header": false }
  ],
  "edges": [
    { "source": "B0", "target": "B1", "label": null, "is_back_edge": false }
  ]
}
```

(`lines` = source lines covered; `instr_ids` = TacInstr ids inside the block; edge `label` is
null, "TRUE" or "FALSE".)

Rules:
- Node ids are "B0", "B1", ... in creation order, per function. START is always B0 with label
  "START"; END has type "end" and label "END".
- A decision node has exactly two outgoing edges labelled "TRUE" and "FALSE".
- if_false: fall-through is TRUE, jump target is FALSE. if_true: the reverse.
- "io" = block whose only work is printf/scanf calls; otherwise "process".
- Labels use the original source text (`src`), never temporaries like t1.
- To show what the optimiser removed, the UI compares instr_ids between the original CFG and the
  optimised CFG. Because instruction ids are stable (section 6), no other mapping is needed.

## 8. API CONTRACT (backend -> frontend)   [Raghav defines with Sneh]

All endpoints: POST, JSON body `{"language": "c", "code": "<source>"}`, path prefix `/api`.
All responses use one envelope, HTTP 200 even for compile errors:

```
{ "ok": true|false,
  "errors":   [Diagnostic],
  "warnings": [Diagnostic],
  "data": { ... } | null }
Diagnostic = { "phase": "lexer|parser|semantic", "severity": "error|warning",
               "message": str, "line": int, "col": int }
```

`ok` is false iff `errors` is non-empty; then `data` is null.

```
POST /api/tokens   data = { "tokens": [ {type, lexeme, line, col} ] }
POST /api/ast      data = { "ast": <AST JSON from section 5> }
POST /api/generate data = { "functions": ["main", ...],
                            "ast": <AST JSON>,
                            "tac":  { "<fn>": [TacInstr JSON] },
                            "cfg":  { "<fn>": <CFG JSON, section 7> },
                            "metrics": { "<fn>": { "nodes": int, "edges": int, "decisions": int,
                                         "loops": int, "cyclomatic_complexity": int } } }
POST /api/optimize data = { "functions": [...],
                            "original":  { "tac": {...}, "cfg": {...}, "metrics": {...} },
                            "optimized": { "tac": {...}, "cfg": {...}, "metrics": {...} },
                            "log": [ LogEntry JSON with keys pass_name, function, line, instr_id,
                                     action, before, after ],
                            "optimized_c": "<C source string>",
                            "warnings_dead_code": [Diagnostic] }
```

Cyclomatic complexity = edges - nodes + 2 (per function CFG).
`run_pipeline(source: str, optimize: bool) -> dict` in `c2f/pipeline.py` returns the same envelope;
`main.py` only wraps it in routes.

## Example payloads

Working examples of every contract live in `backend/tests/fixtures/*.json`. Copies for the UI are in
`frontend/src/mocks/` (kept identical by a test). Until the real stages exist, the backend serves
these fixtures from the real endpoints.
