"""
c2f.optimizer (Ishani)

Public contract (CONTRACTS.md section 6) -- populated as tasks land:
  optimize(prog: TacProgram) -> OptimizeResult(program, log)   [task 5, manager.py]
  OptimizeResult, LogEntry                                      [task 5, manager.py]
  interpret(prog, inputs) -> list[str]                          [task 3, interpreter.py]
  tac_to_c(prog) -> str                                         [stretch, tac_to_c.py]

Not part of the public contract (internal helpers, safe to import directly
within this package only): dataflow.def_use / successors / predecessors /
ReachingDefinitions / LiveVariables.
"""
