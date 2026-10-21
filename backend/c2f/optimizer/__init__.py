"""
c2f.optimizer (Ishani)

Public contract (CONTRACTS.md section 6):
  optimize(prog: TacProgram) -> OptimizeResult(program, log)
  OptimizeResult, LogEntry
  interpret(prog, inputs) -> list[str]
  tac_to_c(prog) -> str   [stretch -- still a stub, raises NotImplementedError]
"""
from c2f.optimizer.manager import LogEntry, OptimizeResult, optimize
from c2f.optimizer.interpreter import interpret
from c2f.optimizer.tac_to_c import tac_to_c

__all__ = ["optimize", "OptimizeResult", "LogEntry", "interpret", "tac_to_c"]
