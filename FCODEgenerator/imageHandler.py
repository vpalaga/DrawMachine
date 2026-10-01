from __future__ import annotations

import math
from collections.abc import Iterable
from pathlib import Path

from PIL import Image, ImageDraw

from gen import PaperSize, paper_size

Point = tuple[float, float]
Bounds = tuple[float, float, float, float]  # min_x, min_y, max_x, max_y
Color = tuple[int, int, int]


class Visual:
    """Simulate the movement of the nozzle and scale the output.

    Drawing moves (pen down) are black, travel moves (pen up) are red and the
    paper area is outlined in blue. The canvas grows beyond the paper if the
    drawing does not fit on it, so nothing is cut off in the preview.
    """

    DRAW_COLOR: Color = (0, 0, 0)
    TRAVEL_COLOR: Color = (255, 0, 0)
    PAPER_COLOR: Color = (0, 120, 255)

    def __init__(
        self,
        size: PaperSize | str,
        scale: float = 1.0,
        bounds: Bounds | None = None,
        margin: float = 5.0,
        max_pixels: int = 8000,
    ) -> None:
        """
        size:       paper name or (x_mm, y_mm)
        scale:      pixels per mm
        bounds:     (min_x, min_y, max_x, max_y) of the drawing in mm; the canvas
                    is enlarged to contain both the paper and these bounds
        margin:     extra border around everything, in mm
        max_pixels: longest allowed canvas side; scale is reduced if exceeded
        """
        self.nozzle_x: float = 0.0
        self.nozzle_y: float = 0.0
        self.pen_is_down: bool = False

        paper_w, paper_h = paper_size(size)
        self.paper_w: float = paper_w
        self.paper_h: float = paper_h

        # world area that must be visible: the paper plus the drawing
        min_x, min_y, max_x, max_y = 0.0, 0.0, float(paper_w), float(paper_h)
        if bounds is not None:
            min_x = min(min_x, bounds[0])
            min_y = min(min_y, bounds[1])
            max_x = max(max_x, bounds[2])
            max_y = max(max_y, bounds[3])

        self.min_x: float = min_x - margin
        self.max_y: float = max_y + margin
        width_mm = (max_x + margin) - self.min_x
        height_mm = self.max_y - (min_y - margin)

        # keep the image at a sane size for very large drawings
        self.scale: float = min(scale, max_pixels / max(width_mm, height_mm))

        self.size_x: int = math.ceil(width_mm * self.scale)
        self.size_y: int = math.ceil(height_mm * self.scale)

        self.img: Image.Image = Image.new("RGB", (self.size_x, self.size_y), color="white")
        self.draw: ImageDraw.ImageDraw = ImageDraw.Draw(self.img)

        self._draw_paper_outline()

    # ----------------------------------------------

    def to_pixel(self, x: float, y: float) -> Point:
        """World (mm, y up) -> image pixels (y down)."""
        return (x - self.min_x) * self.scale, (self.max_y - y) * self.scale

    def _draw_paper_outline(self) -> None:
        corners = [(0, 0), (self.paper_w, 0), (self.paper_w, self.paper_h),
                   (0, self.paper_h), (0, 0)]
        for a, b in zip(corners, corners[1:]):
            self.line(a, b, c=self.PAPER_COLOR)

    # ----------------------------------------------

    def dot(self, pos: Point, c: Color = DRAW_COLOR) -> None:
        self.draw.point(self.to_pixel(*pos), c)

    def plot_points(self, points: Iterable[Point]) -> None:
        for point in points:
            self.dot(point)

    def line(self, start_pos: Point, end_pos: Point, c: Color = DRAW_COLOR) -> None:
        self.draw.line((*self.to_pixel(*start_pos), *self.to_pixel(*end_pos)), c, 1)

    # ----------------------------------------------

    def move(self, x: float, y: float) -> None:
        color = self.DRAW_COLOR if self.pen_is_down else self.TRAVEL_COLOR
        self.line((self.nozzle_x, self.nozzle_y), (x, y), c=color)
        self.nozzle_x, self.nozzle_y = x, y  # update nozzle pos

    def penup(self) -> None:
        self.pen_is_down = False

    def pendown(self) -> None:
        self.pen_is_down = True

    # ----------------------------------------------

    def show(self) -> None:
        self.img.show("drawing")

    def save(self, path: str | Path) -> None:
        self.img.save(path)