from __future__ import annotations

import math
from pathlib import Path

from dxfReader import Reader
from gen import FCODE, paper_size
from imageHandler import Bounds, Visual
from pathOptimizer import optimize_order, travel_distance
from segmentFunctions import Instruction

Point = tuple[float, float]
Polyline = list[Point]


class FGenerator:
    def __init__(
        self,
        path_to_dxf: str | Path,
        acc: float = 0.1,
        vis_scale: float = 10.0,
        text: bool = True,
        paper_format: str = "A4",
        optimize: bool = True,
        center: bool = True,
        join_tol: float = 1e-4,
    ) -> None:
        self.name: str = Path(path_to_dxf).stem
        print(f"name: {self.name}")

        self.acc: float = acc
        self.paper_format: str = paper_format
        self.join_tol: float = join_tol  # max gap at which two polylines count as connected

        self.file = FCODE(size=paper_format, name=self.name)
        self.reader = Reader(name=str(path_to_dxf), acc=acc, text=text)

        # Each polyline is a list of (x, y) points; single points draw nothing.
        self.polylines: list[Polyline] = [
            pl for pl in self.reader.read() if len(pl) >= 2
        ]
        if center:
            self.center_on_paper()
        self._warn_if_off_paper()

        # The preview canvas is sized from the drawing, so nothing gets cut off
        self.vis = Visual(paper_format, scale=vis_scale, bounds=self._bounds())

        # Current machine state
        self._pos: Point = (self.vis.nozzle_x, self.vis.nozzle_y)
        self._pen_is_down: bool = False

        if optimize:
            self.optimize()

    # ----------------------------------------------
    # Placement
    # ----------------------------------------------

    def center_on_paper(self) -> None:
        """Move the whole drawing so its bounding box is centered on the paper.

        DXF files keep their sheet at an arbitrary position (often offset from
        the origin), so without this the drawing lands off-center on the plane.
        """
        bounds = self._bounds()
        if bounds is None:
            return

        min_x, min_y, max_x, max_y = bounds
        width, height = paper_size(self.paper_format)

        dx = width / 2 - (min_x + max_x) / 2
        dy = height / 2 - (min_y + max_y) / 2

        self.polylines = [[(x + dx, y + dy) for x, y in pl] for pl in self.polylines]
        print(f"centered on paper: shifted by ({dx:.1f}, {dy:.1f}) mm")

    # ----------------------------------------------
    # Checks
    # ----------------------------------------------

    def _bounds(self) -> Bounds | None:
        """(min_x, min_y, max_x, max_y) of all polylines, or None if empty."""
        if not self.polylines:
            return None
        xs = [x for pl in self.polylines for x, _ in pl]
        ys = [y for pl in self.polylines for _, y in pl]
        return min(xs), min(ys), max(xs), max(ys)

    def _warn_if_off_paper(self) -> None:
        bounds = self._bounds()
        if bounds is None:
            print("warning: no drawable geometry found in the DXF")
            return

        min_x, min_y, max_x, max_y = bounds
        width, height = paper_size(self.paper_format)

        if min_x < 0 or min_y < 0 or max_x > width or max_y > height:
            print(
                f"warning: drawing bounds x[{min_x:.1f}, {max_x:.1f}] "
                f"y[{min_y:.1f}, {max_y:.1f}] exceed the "
                f"{self.paper_format} plane ({width} x {height} mm)"
            )

    # ----------------------------------------------
    # Path ordering
    # ----------------------------------------------

    def optimize(self) -> None:
        """Reorder the polylines to minimise pen-up travel."""
        before = travel_distance(self.polylines, self._pos)
        self.polylines = optimize_order(self.polylines, start=self._pos)
        after = travel_distance(self.polylines, self._pos)

        saved = (1 - after / before) * 100 if before > 0 else 0.0
        print(f"pen travel: {before:.1f} -> {after:.1f} ({saved:.0f}% less)")

    # ----------------------------------------------
    # Low-level pen commands (keep the file and the preview in sync)
    # ----------------------------------------------

    def _pen_up(self) -> None:
        if self._pen_is_down:
            self.vis.penup()
            self.file.add_instruction(Instruction("PUP"))
            self._pen_is_down = False

    def _pen_down(self) -> None:
        if not self._pen_is_down:
            self.vis.pendown()
            self.file.add_instruction(Instruction("PDN"))
            self._pen_is_down = True

    def _move_to(self, x: float, y: float) -> None:
        self.file.add_instruction(Instruction("MOV", x, y))
        self.vis.move(x, y)
        self._pos = (x, y)

    def _is_at(self, point: Point) -> bool:
        return math.dist(self._pos, point) <= self.join_tol

    # ----------------------------------------------
    # Generation
    # ----------------------------------------------

    def generate_instructions(self) -> None:
        for polyline in self.polylines:
            start = polyline[0]

            # Only lift the pen and travel if we are not already at the start point
            if not self._is_at(start):
                self._pen_up()
                self._move_to(*start)

            self._pen_down()

            for x, y in polyline[1:]:
                self._move_to(x, y)

        self._pen_up()  # leave the pen lifted when finished

    def save(
        self,
        show_visualization: bool = True,
        output_path: str | Path | None = None,
    ) -> None:
        """Write the FCODE file (default: '<name>.FCODE' in the working
        directory) and optionally show the preview."""
        written = self.file.save(output_path)
        print(f"saved: {written}")

        if show_visualization:
            self.vis.show()