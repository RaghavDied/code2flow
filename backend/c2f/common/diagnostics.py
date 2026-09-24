"""Diagnostic: the one error/warning record shared by every compiler phase.

Owner: Raghav. Changes go through a PR that names every teammate (CONTRACTS.md).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

PHASES = ("lexer", "parser", "semantic")
SEVERITIES = ("error", "warning")


@dataclass(frozen=True)
class Diagnostic:
    """A user-facing problem found in the user's C code. Line/col are 1-based."""

    phase: str
    severity: str
    message: str
    line: int
    col: int

    def __post_init__(self) -> None:
        # A bad Diagnostic is a programmer bug, so raising here is allowed.
        if self.phase not in PHASES:
            raise ValueError(f"Diagnostic.phase must be one of {PHASES}, got {self.phase!r}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"Diagnostic.severity must be one of {SEVERITIES}, got {self.severity!r}")
        if self.line < 1 or self.col < 1:
            raise ValueError("Diagnostic line and col are 1-based and must be >= 1")

    def to_dict(self) -> dict:
        """JSON-ready dict with keys phase, severity, message, line, col."""
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Diagnostic":
        """Inverse of to_dict."""
        return Diagnostic(d["phase"], d["severity"], d["message"], d["line"], d["col"])


def make_error(phase: str, message: str, line: int, col: int) -> Diagnostic:
    """Shortcut for an error-severity Diagnostic."""
    return Diagnostic(phase, "error", message, line, col)


def make_warning(phase: str, message: str, line: int, col: int) -> Diagnostic:
    """Shortcut for a warning-severity Diagnostic."""
    return Diagnostic(phase, "warning", message, line, col)
