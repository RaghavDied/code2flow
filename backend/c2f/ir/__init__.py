from .tac import TacFunction, TacInstr, TacProgram, is_literal
from .tac_generator import generate_tac

__all__ = ["generate_tac", "TacInstr", "TacFunction", "TacProgram", "is_literal"]
