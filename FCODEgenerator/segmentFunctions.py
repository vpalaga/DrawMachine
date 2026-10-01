from __future__ import annotations

import math
from typing import ClassVar


class Instruction:
    # instruction name -> number of expected parameters
    instructions_parameters_len: ClassVar[dict[str, int]] = {
        "MOV": 2,
        "PUP": 0,
        "PDN": 0,
        "WAT": 1,
        "CLB": 0,
    }

    def __init__(self, i_type: str, *args: float, acc: float = 0.01) -> None:
        if acc <= 0:
            raise ValueError("acc must be > 0")

        self.i_type: str = i_type.upper()  # instruction type

        # check if the instruction is known and has the right amount of parameters
        if self.i_type not in Instruction.instructions_parameters_len:
            raise ValueError(f"instruction: {self.i_type} is unknown")

        expected = Instruction.instructions_parameters_len[self.i_type]
        if len(args) != expected:
            raise ValueError(
                f"for instruction: {self.i_type} parameters: {list(args)} "
                f"don't match expected length: {expected}"
            )

        # number of decimals to keep: 0.001 -> 3
        self.round_up_to: int = round(-math.log10(acc))

        # parameters as floats; "+ 0.0" turns -0.0 into 0.0
        self.parameters: list[float] = [
            round(float(p), self.round_up_to) + 0.0 for p in args
        ]

    def self_str(self) -> str:
        """String ready for FCODE file writing, e.g. 'MOV 20.05 25.0'."""
        return f"{self.i_type} {' '.join(str(p) for p in self.parameters)}"


if __name__ == "__main__":
    print(Instruction("mov", 20.05, 25).self_str())