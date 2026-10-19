from __future__ import annotations

import math
from collections.abc import Iterable
from pathlib import Path

from dxfReader import Reader
from gen import FCODE, paper_size
from imageHandler import Bounds, Visual
from pathOptimizer import optimize_order, travel_distance
from segmentFunctions import Instruction

Point = tuple[float, float]
Polyline = list[Point]


class FGenerator:
    """Builds an FCODE file (plus a preview) either from a DXF or by hand.

    * ``FGenerator("drawing.dxf")``  -> polylines are read from the DXF; call
      ``generate_instructions()`` to turn them into FCODE.
    * ``FGenerator("my_fcode_name")`` -> no DXF is read, the polylines stay
      empty and you drive the pen yourself with ``pen_up``, ``pen_down``,
      ``move_to``, ``travel_to``, ``draw_to``, ``draw_polyline`` and ``wait``.

    A source counts as a DXF when it ends in ".dxf"; anything else is used as
    the name of the future FCODE file.
    """

    def __init__(
        self,
        source: str | Path,
        acc: float = 0.1,
        vis_scale: float = 10.0,
        text: bool = True,
        paper_format: str = "A4",
        optimize: bool = True,
        center: bool = True,
        join_tol: float = 1e-4,
        head_calibration_after_instruction:int = 200,
        overall_calibration_after_instruction:int = 1000
    ) -> None:
        source_str = str(source)
        self.from_dxf: bool = Path(source_str).suffix.lower() == ".dxf"

        if self.from_dxf:
            self.name: str = Path(source_str).stem
        else:
            name = source_str
            if name.lower().endswith(".fcode"):
                name = name[: -len(".fcode")]
            self.name = name
        print(f"name: {self.name}")

        self.acc: float = acc
        self.paper_format: str = paper_format
        self.join_tol: float = join_tol  # max gap at which two points count as the same
        self._plane: tuple[float, float] = paper_size(paper_format)
        self.head_calibration_after_instruction = head_calibration_after_instruction
        self.overall_calibration_after_instruction = overall_calibration_after_instruction

        self.file = FCODE(size=paper_format, name=self.name)

        # Each polyline is a list of (x, y) points. Stays empty in manual mode.
        self.reader: Reader | None = None
        self.polylines: list[Polyline] = []

        if self.from_dxf:
            self.reader = Reader(name=source_str, acc=acc, text=text)
            self.polylines = [pl for pl in self.reader.read() if len(pl) >= 2]
            if center:
                self.center_on_paper()
            self._warn_if_off_paper()

        # The preview canvas is sized from the drawing, so nothing gets cut off
        self.vis = Visual(paper_format, scale=vis_scale, bounds=self._bounds())

        # Current machine state
        self._pos: Point = (self.vis.nozzle_x, self.vis.nozzle_y)
        self._pen_is_down: bool = False
        self._warned_off_plane: bool = False

        self._head_calibrations:int = 0
        self._calibrations:int = 0

        if self.from_dxf and optimize:
            self.optimize()

    # ----------------------------------------------
    # State
    # ----------------------------------------------

    @property
    def position(self) -> Point:
        return self._pos

    @property
    def pen_is_down(self) -> bool:
        return self._pen_is_down

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
        width, height = self._plane

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
        width, height = self._plane

        if min_x < 0 or min_y < 0 or max_x > width or max_y > height:
            print(
                f"warning: drawing bounds x[{min_x:.1f}, {max_x:.1f}] "
                f"y[{min_y:.1f}, {max_y:.1f}] exceed the "
                f"{self.paper_format} plane ({width} x {height} mm)"
            )

    def _warn_if_off_plane(self, x: float, y: float) -> None:
        """Warn (once) when a manual move leaves the paper plane."""
        width, height = self._plane
        if not self._warned_off_plane and not (0 <= x <= width and 0 <= y <= height):
            self._warned_off_plane = True
            print(
                f"warning: move to ({x:.1f}, {y:.1f}) is outside the "
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
    # Manual commands (file and preview stay in sync)
    # ----------------------------------------------

    def pen_up(self) -> None:
        """Lift the pen (does nothing if it is already up)."""
        if self._pen_is_down:
            self.vis.penup()
            self.file.add_instruction(Instruction("PUP"))
            self._pen_is_down = False

    def pen_down(self) -> None:
        """Lower the pen (does nothing if it is already down)."""
        if not self._pen_is_down:
            self.vis.pendown()
            self.file.add_instruction(Instruction("PDN"))
            self._pen_is_down = True

    def move_to(self, x: float, y: float) -> None:
        """Move to (x, y) in the current pen state: draws if the pen is down."""
        self._warn_if_off_plane(x, y)
        self.file.add_instruction(Instruction("MOV", x, y))
        self.vis.move(x, y)
        self._pos = (x, y)

    def travel_to(self, x: float, y: float) -> None:
        """Lift the pen and move to (x, y) without drawing."""
        self.pen_up()
        self.move_to(x, y)

    def draw_to(self, x: float, y: float) -> None:
        """Lower the pen and draw a line to (x, y)."""
        self.pen_down()
        self.move_to(x, y)

    def draw_polyline(self, points: Iterable[Point]) -> None:
        """Draw through the given points. The pen only lifts and travels to the
        first point if it is not already there."""
        pts = list(points)
        if not pts:
            return

        if not self._is_at(pts[0]):
            self.travel_to(*pts[0])

        self.pen_down()
        for x, y in pts[1:]:
            self.move_to(x, y)

    def wait(self, amount: float) -> None:
        """Insert a WAT instruction."""
        self.file.add_instruction(Instruction("WAT", amount))

    def set_motor_speed(self, xy_sleep_us: int, z_sleep_us: int) -> None:
        """Insert an SMS instruction.

        xy_sleep_us controls the X/Y motor half-cycle sleep on the Pico.
        z_sleep_us controls the Z/head motor speed on the Pico.
        Lower values usually mean faster movement.
        """
        self.file.add_instruction(Instruction("SMS", xy_sleep_us, z_sleep_us))

    def head_calibrate(self):
        self.file.add_instruction(Instruction("HCB"))
        self._pen_is_down = False # moves it up

    def calibrate(self):
        self.file.add_instruction(Instruction("CLB"))
        self._pen_is_down = False # moves it up

    def home(self):
        """adds HOM instruction: HCB and MOV to home pos (MotorController)"""
        self.file.add_instruction(Instruction("HOM"))

    def _is_at(self, point: Point) -> bool:
        return math.dist(self._pos, point) <= self.join_tol

    # ----------------------------------------------
    # Generation
    # ----------------------------------------------

    def generate_instructions(self) -> None:
        """Turn the polylines read from the DXF into instructions."""
        for polyline in self.polylines:
            self.draw_polyline(polyline)

            # count of instructions in the file
            instructions = len(self.file.instructions)
            # do calibrations
            if math.floor(instructions / self.head_calibration_after_instruction) > self._head_calibrations :
                self._head_calibrations += 1
                self.head_calibrate()

            if math.floor(instructions / self.overall_calibration_after_instruction) > self._calibrations:
                self._calibrations += 1
                self.calibrate()



    def save(
        self,
        show_visualization: bool = True,
        output_path: str | Path = Path(".fcodes"),

    ) -> None:
        """Write the FCODE file (default: '<name>.FCODE' in the working
        directory) and optionally show the preview."""
        if isinstance(output_path, str) : output_path:Path = Path(output_path)

        written = self.file.save(output_path)
        print(f"saved: {written}")

        if show_visualization:
            self.vis.show()