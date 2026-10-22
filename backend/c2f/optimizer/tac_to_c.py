
"""Generate basic C source from a TAC program.

TAC does not preserve C type information, so this converter targets a
basic integer-oriented subset and rejects unsupported array instructions.
"""
from __future__ import annotations

import re

from c2f.ir import TacProgram

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_]\w*$")

def _identifier(name: str) -> str:
    """Validate an identifier before emitting it as C source."""
    if not _IDENTIFIER_RE.fullmatch(name):
        raise ValueError(f"Invalid C identifier in TAC: {name!r}")
    return name


def _operand(value: str | None) -> str:
    """Validate and return a TAC operand or literal."""
    if value is None:
        raise ValueError("Missing required TAC operand")

    value = value.strip()
    if not value:
        raise ValueError("Empty TAC operand")

    # Preserve numeric, character, and string literals.
    if re.fullmatch(r"-?\d+", value):
        return value
    if re.fullmatch(r"-?(\d+\.\d*|\.\d+)", value):
        return value
    if re.fullmatch(r"'(\\.|[^'\\])'", value):
        return value
    if re.fullmatch(r'"(\\.|[^"\\])*"', value):
        return value

    # Support the address-of form used by calls such as scanf("%d", &x).
    if value.startswith("&"):
        return "&" + _identifier(value[1:])

    return _identifier(value)


def _instruction(instr) -> str | None:
    """Translate one TAC instruction into a C statement."""
    op = instr.op

    if op == "assign":
        return f"{_identifier(instr.result)} = {_operand(instr.arg1)};"

    if op == "binop":
        left = _operand(instr.arg1)
        right = _operand(instr.arg2)
        return (
            f"{_identifier(instr.result)} = "
            f"({left} {instr.operator} {right});"
        )

    if op == "unop":
        value = _operand(instr.arg1)
        return f"{_identifier(instr.result)} = ({instr.operator}{value});"

    if op == "label":
        label = _identifier(instr.label)
        return f"{label}: ;"

    if op == "goto":
        return f"goto {_identifier(instr.target)};"

    if op == "if_false":
        condition = _operand(instr.arg1)
        target = _identifier(instr.target)
        return f"if (!({condition})) goto {target};"

    if op == "if_true":
        condition = _operand(instr.arg1)
        target = _identifier(instr.target)
        return f"if ({condition}) goto {target};"

    if op == "call":
        function = _identifier(instr.arg1)
        args = ", ".join(_operand(arg) for arg in instr.args)
        call = f"{function}({args})"
        if instr.result:
            return f"{_identifier(instr.result)} = {call};"
        return f"{call};"

    if op == "return":
        if instr.arg1 is None:
            return "return;"
        return f"return {_operand(instr.arg1)};"

    if op in ("array_load", "array_store"):
        raise NotImplementedError(
            f"tac_to_c does not yet support TAC operation {op!r}"
        )

    raise NotImplementedError(f"Unsupported TAC operation: {op!r}")


def tac_to_c(prog: TacProgram) -> str:
    """Convert a TAC program into basic C source."""
    output: list[str] = ["#include <stdio.h>", ""]

    for function in prog.functions.values():
        name = _identifier(function.name)
        params = [_identifier(param) for param in function.params]
        signature = ", ".join(f"int {param}" for param in params) or "void"

        # Gather variables and temporaries that need declarations.
        variables: set[str] = set(params)

        for instr in function.instrs:
            if instr.op in ("array_load", "array_store"):
                raise NotImplementedError(
                    f"tac_to_c does not yet support TAC operation {instr.op!r}"
                )

            if instr.result:
                variables.add(_identifier(instr.result))

            # The function name in a call is not a variable.
            if instr.op != "call" and instr.arg1:
                value = instr.arg1.strip()
                if value.startswith("&"):
                    value = value[1:]
                if _IDENTIFIER_RE.fullmatch(value):
                    variables.add(value)

            if instr.arg2:
                value = instr.arg2.strip()
                if _IDENTIFIER_RE.fullmatch(value):
                    variables.add(value)

            for arg in instr.args:
                value = arg.strip()
                if value.startswith("&"):
                    value = value[1:]
                if _IDENTIFIER_RE.fullmatch(value):
                    variables.add(value)

        # Parameters are already declared in the function signature.
        local_variables = sorted(variables - set(params))
        output.append(f"int {name}({signature}) {{")

        if local_variables:
            output.extend(f"    int {var};" for var in local_variables)
            output.append("")

        for instr in function.instrs:
            statement = _instruction(instr)
            if statement is None:
                continue

            if instr.op == "label":
                # A C label must start a statement and cannot be indented
                # as though it were an ordinary statement.
                output.append(f"{statement}")
            else:
                output.append(f"    {statement}")

        output.append("}")
        output.append("")

    return "\n".join(output)
