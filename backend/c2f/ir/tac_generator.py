"""AST -> Three-Address Code (TAC) lowering (CONTRACTS.md section 6).

Owner: Raghav.
Translates an AST Program into TacProgram with stable unique instruction IDs,
proper temporaries (^t[0-9]+$), labels (L0, L1, ...), and clean source text.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from c2f.semantic.ast_nodes import (
    ArrayAccess,
    Assign,
    BinaryOp,
    Block,
    Break,
    Call,
    Case,
    Continue,
    DoWhile,
    Expr,
    ExprStmt,
    For,
    Function,
    Identifier,
    If,
    Literal,
    Node,
    Program,
    Return,
    Stmt,
    Switch,
    UnaryOp,
    VarDecl,
    While,
)

from .tac import TacFunction, TacInstr, TacProgram


def _to_src(node: Optional[Node]) -> str:
    """Format an AST node into clean source representation for flowchart display."""
    if node is None:
        return ""
    if isinstance(node, Literal):
        return node.value
    if isinstance(node, Identifier):
        return node.name
    if isinstance(node, ArrayAccess):
        return f"{node.name}[{_to_src(node.index)}]"
    if isinstance(node, BinaryOp):
        return f"{_to_src(node.left)} {node.op} {_to_src(node.right)}"
    if isinstance(node, UnaryOp):
        return f"{_to_src(node.operand)}{node.op}" if node.postfix else f"{node.op}{_to_src(node.operand)}"
    if isinstance(node, Assign):
        return f"{_to_src(node.target)} {node.op} {_to_src(node.value)}"
    if isinstance(node, Call):
        args_str = ", ".join(_to_src(a) for a in node.args)
        return f"{node.name}({args_str})"
    if isinstance(node, Return):
        return f"return {_to_src(node.value)}" if node.value else "return"
    if isinstance(node, VarDecl):
        if node.init is not None:
            return f"{node.var_type} {node.name} = {_to_src(node.init)}"
        return f"{node.var_type} {node.name}"
    return ""


class TacGenerator:
    """Lowers an AST Program into three-address code."""

    def __init__(self) -> None:
        self.next_instr_id: int = 1

    def generate(self, prog: Program) -> TacProgram:
        functions: Dict[str, TacFunction] = {}
        for fn in getattr(prog, "functions", []):
            if isinstance(fn, Function):
                functions[fn.name] = self.generate_function(fn)
        return TacProgram(functions=functions)

    def generate_function(self, fn: Function) -> TacFunction:
        instrs: List[TacInstr] = []
        temp_counter: int = 1
        label_counter: int = 0
        loop_stack: List[dict] = []  # dicts with keys "continue" and "break"

        def new_temp() -> str:
            nonlocal temp_counter
            t = f"t{temp_counter}"
            temp_counter += 1
            return t

        def new_label() -> str:
            nonlocal label_counter
            lbl = f"L{label_counter}"
            label_counter += 1
            return lbl

        def emit(
            op: str,
            result: Optional[str] = None,
            arg1: Optional[str] = None,
            arg2: Optional[str] = None,
            operator: Optional[str] = None,
            target: Optional[str] = None,
            label: Optional[str] = None,
            args: Optional[List[str]] = None,
            line: int = 1,
            src: str = "",
        ) -> TacInstr:
            instr = TacInstr(
                id=self.next_instr_id,
                op=op,
                result=result,
                arg1=arg1,
                arg2=arg2,
                operator=operator,
                target=target,
                label=label,
                args=args or [],
                line=line,
                src=src,
            )
            self.next_instr_id += 1
            instrs.append(instr)
            return instr

        def emit_expr(expr: Optional[Expr]) -> str:
            if expr is None:
                return ""

            if isinstance(expr, Literal):
                return expr.value

            if isinstance(expr, Identifier):
                return expr.name

            if isinstance(expr, ArrayAccess):
                idx = emit_expr(expr.index)
                t = new_temp()
                emit(
                    op="array_load",
                    result=t,
                    arg1=expr.name,
                    arg2=idx,
                    line=expr.line,
                    src=_to_src(expr),
                )
                return t

            if isinstance(expr, BinaryOp):
                l = emit_expr(expr.left)
                r = emit_expr(expr.right)
                t = new_temp()
                emit(
                    op="binop",
                    result=t,
                    arg1=l,
                    operator=expr.op,
                    arg2=r,
                    line=expr.line,
                    src=_to_src(expr),
                )
                return t

            if isinstance(expr, UnaryOp):
                if expr.op in ("-", "!"):
                    operand = emit_expr(expr.operand)
                    t = new_temp()
                    emit(
                        op="unop",
                        result=t,
                        operator=expr.op,
                        arg1=operand,
                        line=expr.line,
                        src=_to_src(expr),
                    )
                    return t
                if expr.op == "&":
                    # Address-of operand (e.g. scanf("%d", &x))
                    return f"&{_to_src(expr.operand)}"
                if expr.op in ("++", "--"):
                    target_name = expr.operand.name if isinstance(expr.operand, Identifier) else _to_src(expr.operand)
                    arith_op = "+" if expr.op == "++" else "-"
                    if expr.postfix:
                        old_t = new_temp()
                        emit("assign", result=old_t, arg1=target_name, line=expr.line, src=_to_src(expr))
                        inc_t = new_temp()
                        emit("binop", result=inc_t, arg1=target_name, operator=arith_op, arg2="1", line=expr.line, src=f"{target_name} {arith_op} 1")
                        emit("assign", result=target_name, arg1=inc_t, line=expr.line, src=f"{target_name} = {inc_t}")
                        return old_t
                    else:
                        inc_t = new_temp()
                        emit("binop", result=inc_t, arg1=target_name, operator=arith_op, arg2="1", line=expr.line, src=f"{target_name} {arith_op} 1")
                        emit("assign", result=target_name, arg1=inc_t, line=expr.line, src=f"{target_name} = {inc_t}")
                        return target_name

            if isinstance(expr, Assign):
                val = emit_expr(expr.value)
                if expr.op != "=":
                    # Compound assignment +=, -=, *=, /=
                    bin_op = expr.op[0]
                    target_repr = expr.target.name if isinstance(expr.target, Identifier) else _to_src(expr.target)
                    compound_t = new_temp()
                    emit("binop", result=compound_t, arg1=target_repr, operator=bin_op, arg2=val, line=expr.line, src=f"{target_repr} {bin_op} {val}")
                    val = compound_t

                if isinstance(expr.target, ArrayAccess):
                    idx = emit_expr(expr.target.index)
                    emit("array_store", result=val, arg1=expr.target.name, arg2=idx, line=expr.line, src=_to_src(expr))
                else:
                    target_name = expr.target.name if isinstance(expr.target, Identifier) else _to_src(expr.target)
                    emit("assign", result=target_name, arg1=val, line=expr.line, src=_to_src(expr))
                return val

            if isinstance(expr, Call):
                arg_vals = [emit_expr(a) for a in expr.args]
                t = new_temp()
                emit("call", result=t, arg1=expr.name, args=arg_vals, line=expr.line, src=_to_src(expr))
                return t

            return ""

        def emit_stmt(stmt: Optional[Stmt]) -> None:
            if stmt is None:
                return

            if isinstance(stmt, Block):
                for s in getattr(stmt, "statements", []):
                    emit_stmt(s)

            elif isinstance(stmt, VarDecl):
                if stmt.init is not None:
                    val = emit_expr(stmt.init)
                    emit("assign", result=stmt.name, arg1=val, line=stmt.line, src=_to_src(stmt))

            elif isinstance(stmt, ExprStmt):
                if isinstance(stmt.expr, Call):
                    arg_vals = [emit_expr(a) for a in stmt.expr.args]
                    emit("call", result=None, arg1=stmt.expr.name, args=arg_vals, line=stmt.line, src=_to_src(stmt.expr))
                elif isinstance(stmt.expr, UnaryOp) and stmt.expr.op in ("++", "--"):
                    target_name = stmt.expr.operand.name if isinstance(stmt.expr.operand, Identifier) else _to_src(stmt.expr.operand)
                    arith_op = "+" if stmt.expr.op == "++" else "-"
                    inc_t = new_temp()
                    emit("binop", result=inc_t, arg1=target_name, operator=arith_op, arg2="1", line=stmt.line, src=f"{target_name} {arith_op} 1")
                    emit("assign", result=target_name, arg1=inc_t, line=stmt.line, src=_to_src(stmt.expr))
                else:
                    emit_expr(stmt.expr)

            elif isinstance(stmt, If):
                cond_src = _to_src(stmt.cond)
                cond_val = emit_expr(stmt.cond)
                if stmt.else_ is None:
                    l_end = new_label()
                    emit("if_false", arg1=cond_val, target=l_end, line=stmt.cond.line, src=cond_src)
                    emit_stmt(stmt.then)
                    emit("label", label=l_end, line=stmt.line, src=f"{l_end}:")
                else:
                    l_else = new_label()
                    l_end = new_label()
                    emit("if_false", arg1=cond_val, target=l_else, line=stmt.cond.line, src=cond_src)
                    emit_stmt(stmt.then)
                    emit("goto", target=l_end, line=stmt.line, src=f"goto {l_end}")
                    emit("label", label=l_else, line=getattr(stmt.else_, "line", stmt.line), src=f"{l_else}:")
                    emit_stmt(stmt.else_)
                    emit("label", label=l_end, line=stmt.line, src=f"{l_end}:")

            elif isinstance(stmt, While):
                l_cond = new_label()
                l_end = new_label()
                loop_stack.append({"continue": l_cond, "break": l_end})
                emit("label", label=l_cond, line=stmt.line, src=f"{l_cond}:")
                cond_src = _to_src(stmt.cond)
                cond_val = emit_expr(stmt.cond)
                emit("if_false", arg1=cond_val, target=l_end, line=stmt.cond.line, src=cond_src)
                emit_stmt(stmt.body)
                emit("goto", target=l_cond, line=stmt.line, src=f"goto {l_cond}")
                emit("label", label=l_end, line=stmt.line, src=f"{l_end}:")
                loop_stack.pop()

            elif isinstance(stmt, DoWhile):
                l_body = new_label()
                l_cond = new_label()
                l_end = new_label()
                loop_stack.append({"continue": l_cond, "break": l_end})
                emit("label", label=l_body, line=stmt.line, src=f"{l_body}:")
                emit_stmt(stmt.body)
                emit("label", label=l_cond, line=stmt.cond.line, src=f"{l_cond}:")
                cond_src = _to_src(stmt.cond)
                cond_val = emit_expr(stmt.cond)
                emit("if_true", arg1=cond_val, target=l_body, line=stmt.cond.line, src=cond_src)
                emit("label", label=l_end, line=stmt.line, src=f"{l_end}:")
                loop_stack.pop()

            elif isinstance(stmt, For):
                l_cond = new_label()
                l_update = new_label()
                l_end = new_label()
                loop_stack.append({"continue": l_update, "break": l_end})
                if stmt.init is not None:
                    emit_stmt(stmt.init)
                emit("label", label=l_cond, line=stmt.line, src=f"{l_cond}:")
                if stmt.cond is not None:
                    cond_src = _to_src(stmt.cond)
                    cond_val = emit_expr(stmt.cond)
                    emit("if_false", arg1=cond_val, target=l_end, line=stmt.cond.line, src=cond_src)
                emit_stmt(stmt.body)
                emit("label", label=l_update, line=getattr(stmt.update, "line", stmt.line), src=f"{l_update}:")
                if stmt.update is not None:
                    emit_expr(stmt.update)
                emit("goto", target=l_cond, line=stmt.line, src=f"goto {l_cond}")
                emit("label", label=l_end, line=stmt.line, src=f"{l_end}:")
                loop_stack.pop()

            elif isinstance(stmt, Switch):
                switch_val = emit_expr(stmt.expr)
                l_end = new_label()
                loop_stack.append({"continue": None, "break": l_end})
                cases = getattr(stmt, "cases", [])
                case_labels = [new_label() for _ in cases]
                default_label = None

                for idx, c in enumerate(cases):
                    if c.value is None:
                        default_label = case_labels[idx]
                    else:
                        c_val = emit_expr(c.value)
                        cmp_t = new_temp()
                        emit("binop", result=cmp_t, arg1=switch_val, operator="==", arg2=c_val, line=c.line, src=f"{switch_val} == {c_val}")
                        emit("if_true", arg1=cmp_t, target=case_labels[idx], line=c.line, src=f"{switch_val} == {c_val}")

                if default_label is not None:
                    emit("goto", target=default_label, line=stmt.line, src=f"goto {default_label}")
                else:
                    emit("goto", target=l_end, line=stmt.line, src=f"goto {l_end}")

                for idx, c in enumerate(cases):
                    emit("label", label=case_labels[idx], line=c.line, src=f"{case_labels[idx]}:")
                    for st in getattr(c, "body", []):
                        emit_stmt(st)

                emit("label", label=l_end, line=stmt.line, src=f"{l_end}:")
                loop_stack.pop()

            elif isinstance(stmt, Break):
                if loop_stack and loop_stack[-1]["break"]:
                    emit("goto", target=loop_stack[-1]["break"], line=stmt.line, src="break;")

            elif isinstance(stmt, Continue):
                if loop_stack and loop_stack[-1]["continue"]:
                    emit("goto", target=loop_stack[-1]["continue"], line=stmt.line, src="continue;")

            elif isinstance(stmt, Return):
                if stmt.value is not None:
                    v = emit_expr(stmt.value)
                    emit("return", arg1=v, line=stmt.line, src=_to_src(stmt))
                else:
                    emit("return", line=stmt.line, src="return")

        # Emit function body
        if isinstance(fn.body, Block):
            for s in fn.body.statements:
                emit_stmt(s)
        elif fn.body is not None:
            emit_stmt(fn.body)

        # CONTRACTS.md Section 6: "Every function ends with an explicit return."
        if not instrs or instrs[-1].op != "return":
            emit("return", line=fn.line, src="return")

        param_names = [p.get("name", "") for p in fn.params if p.get("name")]
        return TacFunction(name=fn.name, params=param_names, instrs=instrs)


def generate_tac(ast: Program) -> TacProgram:
    """Lower an AST Program into Three-Address Code."""
    generator = TacGenerator()
    return generator.generate(ast)
