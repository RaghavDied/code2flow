"""
c2f/optimizer/_support.py (Ishani)

Shared helpers for the core passes -- not part of the public contract.
"""
from __future__ import annotations

from typing import Any


def parse_literal(text: str) -> Any:
    if text.startswith('"') or text.startswith("'"):
        inner = text[1:-1]
        return (
            inner.replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace('\\"', '"')
            .replace("\\'", "'")
            .replace("\\\\", "\\")
        )
    if "." in text:
        return float(text)
    return int(text)


def format_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        s = repr(value)
        if "." not in s and "e" not in s:
            s += ".0"
        return s
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def apply_binop(op: str, a: Any, b: Any) -> Any:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if isinstance(a, int) and isinstance(b, int):
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
    raise ValueError(f"unknown binop operator {op!r}")


def apply_unop(op: str, a: Any) -> Any:
    if op == "-":
        return -a
    if op == "!":
        return int(not bool(a))
    raise ValueError(f"unknown unop operator {op!r}")


def render(instr) -> str:
    """Human-readable one-line text for LogEntry.before/after, e.g. 't1 = 2 * 3'."""
    op = instr.op
    if op == "assign":
        return f"{instr.result} = {instr.arg1}"
    if op == "binop":
        return f"{instr.result} = {instr.arg1} {instr.operator} {instr.arg2}"
    if op == "unop":
        return f"{instr.result} = {instr.operator}{instr.arg1}"
    if op == "label":
        return f"{instr.label}:"
    if op == "goto":
        return f"goto {instr.target}"
    if op == "if_false":
        return f"if_false {instr.arg1} goto {instr.target}"
    if op == "if_true":
        return f"if_true {instr.arg1} goto {instr.target}"
    if op == "call":
        call_text = f"call {instr.arg1}({', '.join(instr.args)})"
        return f"{instr.result} = {call_text}" if instr.result else call_text
    if op == "return":
        return f"return {instr.arg1}" if instr.arg1 is not None else "return"
    if op == "array_load":
        return f"{instr.result} = {instr.arg1}[{instr.arg2}]"
    if op == "array_store":
        return f"{instr.arg1}[{instr.arg2}] = {instr.result}"
    return f"{op} {instr.id}"
