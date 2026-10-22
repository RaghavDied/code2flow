"""Scoped symbol table for semantic analysis.

Owner: Raghav (CONTRACTS.md section 5).
Tracks scopes, variables, functions, and array symbols with type information.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Symbol:
    """One declared identifier in the symbol table."""

    name: str
    type: str  # "int" | "float" | "char" | "void" | "string"
    line: int = 1
    col: int = 1
    is_function: bool = False
    is_array: bool = False
    array_size: Optional[int] = None
    params: List[dict] = field(default_factory=list)  # [{"type": str, "name": str}]


class Scope:
    """A single lexical scope with an optional enclosing parent scope."""

    def __init__(self, parent: Optional["Scope"] = None) -> None:
        self.parent: Optional[Scope] = parent
        self.symbols: Dict[str, Symbol] = {}

    def define(self, sym: Symbol) -> bool:
        """Define a symbol in this scope.

        Returns False if already defined in the SAME scope (redeclaration error).
        """
        if sym.name in self.symbols:
            return False
        self.symbols[sym.name] = sym
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up symbol from this scope outwards to parent scopes."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    def lookup_current(self, name: str) -> Optional[Symbol]:
        """Look up symbol strictly in this scope (for redeclaration checks)."""
        return self.symbols.get(name)


class SymbolTable:
    """Scoped symbol table with built-in C functions pre-registered."""

    def __init__(self) -> None:
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register built-in C I/O functions: printf and scanf."""
        self.global_scope.define(
            Symbol(name="printf", type="int", is_function=True, params=[])
        )
        self.global_scope.define(
            Symbol(name="scanf", type="int", is_function=True, params=[])
        )

    def enter_scope(self) -> Scope:
        """Push a new nested scope."""
        new_scope = Scope(parent=self.current_scope)
        self.current_scope = new_scope
        return new_scope

    def exit_scope(self) -> Scope:
        """Pop the current scope and return to the parent scope."""
        if self.current_scope.parent is not None:
            self.current_scope = self.current_scope.parent
        return self.current_scope

    def define(self, sym: Symbol) -> bool:
        """Define symbol in the current scope."""
        return self.current_scope.define(sym)

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up symbol by name in current scope chain."""
        return self.current_scope.lookup(name)

    def lookup_current(self, name: str) -> Optional[Symbol]:
        """Look up symbol strictly in the current scope."""
        return self.current_scope.lookup_current(name)

    @property
    def is_global(self) -> bool:
        """True if the current scope is the top-level global scope."""
        return self.current_scope.parent is None
