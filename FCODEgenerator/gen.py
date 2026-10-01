from __future__ import annotations

from pathlib import Path

from segmentFunctions import Instruction

PaperSize = tuple[float, float]

PAPER_SIZES: dict[str, PaperSize] = {  # in mm (x, y)
    "A5": (210, 148),
    "A4": (297, 210),
    "A3": (420, 297),
}


def paper_size(size: PaperSize | str) -> PaperSize:
    """Resolve a paper name ('A4') or an (x_mm, y_mm) tuple to (x_mm, y_mm)."""
    if isinstance(size, str):
        try:
            return PAPER_SIZES[size.upper()]
        except KeyError:
            raise KeyError(f"Paper size: {{{size}}} is invalid") from None
    return size[0], size[1]


class FCODE:
    def __init__(self, size: PaperSize | str, name: str) -> None:
        plane = paper_size(size)

        self.name: str = name
        self.header: dict[str, object] = {
            "header_length": -1,
            "name": name,
            "plane_size_mm": plane,
        }
        self.header["header_length"] = len(self.header)

        self.instructions: list[Instruction] = []

    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions.append(instruction)

    def save(self, path: str | Path | None = None) -> Path:
        """Write the FCODE file. Defaults to '<name>.FCODE' in the working
        directory. Returns the path that was written."""
        target = Path(path) if path is not None else Path(f"{self.name}.FCODE")

        with open(target, "w", encoding="utf-8") as file:
            for key, value in self.header.items():
                file.write(f"{key} {value}\n")

            for instruction in self.instructions:
                file.write(instruction.self_str() + "\n")

        return target