"""
c2f/optimizer/interpreter.py  (Ishani)

interpret(prog: TacProgram, inputs: list[str]) -> list[str]

Runs `main` (with no arguments) over the TAC instructions, following
label/goto/if_true/if_false control flow exactly, and returns the list of
printf output lines produced. `inputs` feeds scanf calls, one token per
variable read, in program order. This is the correctness oracle every
optimisation pass is checked against: interpret(original) must equal
interpret(optimised) for the same inputs.

Supported ops: assign, binop, unop, label, goto, if_false, if_true, call
(printf, scanf, user-defined function calls), return, array_load, array_store.
"""
from __future__ import annotations

from typing import Any

from c2f.ir import TacFunction, TacProgram, is_literal


class TacRuntimeError(Exception):
    """Raised for malformed TAC (undefined label, undefined variable, etc)."""


def _strip_quotes_and_unescape(text: str) -> str:
    """'"hi\\n"' -> 'hi\\n' (actual newline); "'a'" -> 'a'."""
    inner = text[1:-1]
    return (
        inner.replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .replace("\\\\", "\\")
    )


def _parse_literal(text: str) -> Any:
    if text.startswith('"') or text.startswith("'"):
        return _strip_quotes_and_unescape(text)
    if "." in text:
        return float(text)
    return int(text)


def _parse_input_token(token: str) -> Any:
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return token


class _Env(dict):
    """Variable environment for one function-call frame."""


def _eval_operand(operand: str | None, env: _Env) -> Any:
    if operand is None:
        return None
    if is_literal(operand):
        return _parse_literal(operand)
    if operand not in env:
        raise TacRuntimeError(f"use of undefined variable {operand!r}")
    return env[operand]


def _apply_binop(op: str, a: Any, b: Any) -> Any:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if isinstance(a, int) and isinstance(b, int):
            # C integer division truncates toward zero
            q = abs(a) // abs(b)
            return -q if (a < 0) != (b < 0) else q
        return a / b
    if op == "%":
        r = abs(a) % abs(b)
        return -r if a < 0 else r
    if op == "<":
        return int(a < b)
    if op == "<=":
        return int(a <= b)
    if op == ">":
        return int(a > b)
    if op == ">=":
        return int(a >= b)
    if op == "==":
        return int(a == b)
    if op == "!=":
        return int(a != b)
    if op == "&&":
        return int(bool(a) and bool(b))
    if op == "||":
        return int(bool(a) or bool(b))
    raise TacRuntimeError(f"unknown binop operator {op!r}")


def _apply_unop(op: str, a: Any) -> Any:
    if op == "-":
        return -a
    if op == "!":
        return int(not bool(a))
    raise TacRuntimeError(f"unknown unop operator {op!r}")


_PRINTF_SPECIFIERS = ("%d", "%f", "%c", "%s")


def _format_printf(fmt: str, values: list[Any]) -> str:
    out = []
    i = 0
    vi = 0
    while i < len(fmt):
        if fmt[i : i + 2] in _PRINTF_SPECIFIERS:
            out.append(str(values[vi]))
            vi += 1
            i += 2
        else:
            out.append(fmt[i])
            i += 1
    return "".join(out)


class _InputCursor:
    def __init__(self, inputs: list[str]):
        self._tokens = list(inputs)
        self._i = 0

    def next(self) -> Any:
        if self._i >= len(self._tokens):
            raise TacRuntimeError("scanf ran out of `inputs`")
        token = self._tokens[self._i]
        self._i += 1
        return _parse_input_token(token)


class _Interpreter:
    def __init__(self, prog: TacProgram, inputs: list[str]):
        self.prog = prog
        self.output: list[str] = []
        self.cursor = _InputCursor(inputs)

    def run(self, fn_name: str, args: list[Any]) -> Any:
        fn = self.prog.functions[fn_name]
        env = _Env(zip(fn.params, args))
        return self._run_function(fn, env)

    def _run_function(self, fn: TacFunction, env: _Env) -> Any:
        label_index = {
            instr.label: i for i, instr in enumerate(fn.instrs) if instr.op == "label"
        }
        pc = 0
        n = len(fn.instrs)
        while pc < n:
            instr = fn.instrs[pc]
            op = instr.op

            if op == "assign":
                env[instr.result] = _eval_operand(instr.arg1, env)
                pc += 1
            elif op == "binop":
                a = _eval_operand(instr.arg1, env)
                b = _eval_operand(instr.arg2, env)
                env[instr.result] = _apply_binop(instr.operator, a, b)
                pc += 1
            elif op == "unop":
                a = _eval_operand(instr.arg1, env)
                env[instr.result] = _apply_unop(instr.operator, a)
                pc += 1
            elif op == "label":
                pc += 1
            elif op == "goto":
                pc = label_index[instr.target]
            elif op == "if_false":
                cond = _eval_operand(instr.arg1, env)
                pc = label_index[instr.target] if not cond else pc + 1
            elif op == "if_true":
                cond = _eval_operand(instr.arg1, env)
                pc = label_index[instr.target] if cond else pc + 1
            elif op == "call":
                result = self._run_call(instr, env)
                if instr.result is not None:
                    env[instr.result] = result
                pc += 1
            elif op == "return":
                return _eval_operand(instr.arg1, env) if instr.arg1 is not None else None
            elif op == "array_load":
                arr = env.setdefault(instr.arg1, {})
                idx = _eval_operand(instr.arg2, env)
                env[instr.result] = arr.get(idx, 0)
                pc += 1
            elif op == "array_store":
                arr = env.setdefault(instr.arg1, {})
                idx = _eval_operand(instr.arg2, env)
                arr[idx] = _eval_operand(instr.result, env)
                pc += 1
            else:
                raise TacRuntimeError(f"unknown op {op!r}")
        return None  # fell off the end without an explicit return

    def _run_call(self, instr, env: _Env):
        fn_name = instr.arg1
        if fn_name == "printf":
            fmt = _parse_literal(instr.args[0])
            values = [_eval_operand(a, env) for a in instr.args[1:]]
            self.output.append(_format_printf(fmt, values))
            return None
        if fn_name == "scanf":
            # args[0] is the format string; the rest are "&varname" targets
            for target in instr.args[1:]:
                var = target[1:] if target.startswith("&") else target
                env[var] = self.cursor.next()
            return None
        if fn_name in self.prog.functions:
            arg_values = [_eval_operand(a, env) for a in instr.args]
            return self.run(fn_name, arg_values)
        raise TacRuntimeError(f"call to unknown function {fn_name!r}")


def interpret(prog: TacProgram, inputs: list[str]) -> list[str]:
    """Run `main()` and return the captured printf output lines, in order."""
    interp = _Interpreter(prog, inputs)
    interp.run("main", [])
    return interp.output
