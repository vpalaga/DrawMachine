from __future__ import annotations

import logging
import math
from collections.abc import Iterable, Iterator

import ezdxf
from ezdxf.addons import text2path
from ezdxf.document import Drawing
from ezdxf.entities import Arc, Circle, DXFEntity, Ellipse, MText, Text
from ezdxf.entities import Point as DxfPoint
from ezdxf.enums import TextEntityAlignment
from ezdxf.layouts import Modelspace
from ezdxf.lldxf.const import (
    MTEXT_TOP_LEFT, MTEXT_TOP_CENTER, MTEXT_TOP_RIGHT,
    MTEXT_MIDDLE_LEFT, MTEXT_MIDDLE_CENTER, MTEXT_MIDDLE_RIGHT,
    MTEXT_BOTTOM_LEFT, MTEXT_BOTTOM_CENTER, MTEXT_BOTTOM_RIGHT,
)
from ezdxf.path import Path, make_path

logger = logging.getLogger(__name__)

Point = tuple[float, float]
Polyline = list[Point]

MAX_INSERT_DEPTH = 16

# Built once instead of on every MTEXT call
_ATTACH_MAP: dict[int, TextEntityAlignment] = {
    MTEXT_TOP_LEFT: TextEntityAlignment.TOP_LEFT,
    MTEXT_TOP_CENTER: TextEntityAlignment.TOP_CENTER,
    MTEXT_TOP_RIGHT: TextEntityAlignment.TOP_RIGHT,
    MTEXT_MIDDLE_LEFT: TextEntityAlignment.MIDDLE_LEFT,
    MTEXT_MIDDLE_CENTER: TextEntityAlignment.MIDDLE_CENTER,
    MTEXT_MIDDLE_RIGHT: TextEntityAlignment.MIDDLE_RIGHT,
    MTEXT_BOTTOM_LEFT: TextEntityAlignment.BOTTOM_LEFT,
    MTEXT_BOTTOM_CENTER: TextEntityAlignment.BOTTOM_CENTER,
    MTEXT_BOTTOM_RIGHT: TextEntityAlignment.BOTTOM_RIGHT,
}


# --------------------------------------------------
# Geometry helpers
# --------------------------------------------------

def gen_circle(center: Point, r: float, segments: int) -> Polyline:
    segments = max(8, segments)
    cx, cy = center
    pts: Polyline = [
        (cx + r * math.cos(2 * math.pi * i / segments),
         cy + r * math.sin(2 * math.pi * i / segments))
        for i in range(segments)
    ]
    pts.append(pts[0])  # close loop
    return pts


def circle_to_polyline(circle: Circle, line_len: float) -> Polyline:
    center = circle.dxf.center
    r = circle.dxf.radius
    segments = max(8, round((2 * math.pi * r) / line_len))
    return gen_circle((center.x, center.y), r, segments)


def ellipse_to_polyline(ellipse: Ellipse, line_len: float) -> Polyline:
    center = ellipse.dxf.center
    major = ellipse.dxf.major_axis
    ratio = ellipse.dxf.ratio
    start = ellipse.dxf.start_param
    end = ellipse.dxf.end_param
    if end <= start:
        end += 2 * math.pi

    a = major.magnitude
    b = a * ratio

    # Ramanujan approximation of the full circumference,
    # scaled to the portion of the ellipse that is actually drawn.
    full_circ = math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))
    circ = full_circ * (end - start) / (2 * math.pi)
    segments = max(8, round(circ / line_len))

    angle = math.atan2(major.y, major.x)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    pts: Polyline = []
    for i in range(segments + 1):
        t = start + (end - start) * i / segments
        x = a * math.cos(t)
        y = b * math.sin(t)
        pts.append((center.x + x * cos_a - y * sin_a,
                    center.y + x * sin_a + y * cos_a))
    return pts


def sagitta_for_chord(r: float, chord: float) -> float:
    """Max deviation of a chord of the given length on a circle of radius r."""
    if r <= 0:
        return 1e-6
    half = min(chord / 2, r)
    return max(1e-6, r - math.sqrt(r * r - half * half))


def path_to_polylines(path: Path, distance: float) -> list[Polyline]:
    """Flatten a path. Each sub-path becomes its own polyline, so separate
    contours (e.g. glyph holes) are not joined by stray connecting lines."""
    result: list[Polyline] = []
    for sub in path.sub_paths():
        pts: Polyline = [(v.x, v.y) for v in sub.flattening(distance=distance)]
        if len(pts) >= 2:
            result.append(pts)
    return result


def entity_to_polylines(entity: DXFEntity, distance: float) -> list[Polyline]:
    return path_to_polylines(make_path(entity), distance)


def generate_hatch_lines(shape_pts: list[Point], spacing: float) -> list[Polyline]:
    """Horizontal hatch lines clipped to the polygon (even-odd rule)."""
    if spacing <= 0:
        raise ValueError("spacing must be > 0")
    if len(shape_pts) < 3:
        return []

    ys = [p[1] for p in shape_pts]
    y_min, y_max = min(ys), max(ys)
    n = len(shape_pts)

    lines: list[Polyline] = []
    for i in range(int((y_max - y_min) / spacing) + 1):
        y = y_min + i * spacing
        xs: list[float] = []
        for j in range(n):
            x1, y1 = shape_pts[j]
            x2, y2 = shape_pts[(j + 1) % n]
            if (y1 <= y < y2) or (y2 <= y < y1):  # half-open: no double counts at vertices
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            lines.append([(xs[k], y), (xs[k + 1], y)])
    return lines


def point_entity(entity: DxfPoint, radius: float, line_len: float) -> Polyline:
    center = entity.dxf.location
    segments = max(8, round((2 * math.pi * radius) / line_len))
    return gen_circle((center.x, center.y), radius, segments)


# --------------------------------------------------
# TEXT handling
# --------------------------------------------------

def mtext_to_texts(mtext: MText, doc: Drawing) -> list[Text]:
    """Split an MTEXT into one *virtual* TEXT entity per line.

    The entities are not added to any layout, so the drawing is not modified.
    """
    lines: list[str] = mtext.plain_text(split=True)
    if not lines:
        return []

    x0, y0, z0 = mtext.dxf.insert
    height: float = mtext.dxf.get("char_height", 1.0)
    rotation: float = mtext.get_rotation()
    attach: int = mtext.dxf.get("attachment_point", MTEXT_TOP_LEFT)
    align = _ATTACH_MAP.get(attach, TextEntityAlignment.TOP_LEFT)

    # MTEXT default line pitch is 5/3 of the text height
    step = height * (5 / 3) * mtext.dxf.get("line_spacing_factor", 1.0)

    # Vertical anchor: 0 = top, 1 = middle, 2 = bottom
    v_anchor = (attach - 1) // 3 if attach in _ATTACH_MAP else 0
    block_height = (len(lines) - 1) * step
    first_offset = (0.0, block_height / 2, block_height)[v_anchor]

    rot = math.radians(rotation)
    cos_r, sin_r = math.cos(rot), math.sin(rot)

    texts: list[Text] = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue

        local_y = first_offset - i * step  # offset along the text's own "up" axis
        dx = -local_y * sin_r
        dy = local_y * cos_r

        t = Text.new(
            dxfattribs={
                "text": line,
                "height": height,
                "rotation": rotation,
                "style": mtext.dxf.get("style", "Standard"),
            },
            doc=doc,
        )
        t.set_placement((x0 + dx, y0 + dy, z0), align=align)
        texts.append(t)
    return texts


# --------------------------------------------------
# Reader
# --------------------------------------------------

class Reader:
    def __init__(
        self,
        name: str,
        acc: float = 0.5,
        text: bool = True,
        debug: bool = False,
        point_radius: float = 0.3,
    ) -> None:
        self.name: str = name
        self.acc: float = max(1e-6, acc)
        self.text: bool = text
        self.debug: bool = debug
        self.point_radius: float = point_radius

        try:
            self.doc: Drawing = ezdxf.readfile(name)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Invalid file: {name}") from exc
        except ezdxf.DXFStructureError as exc:
            raise ValueError(f"Unreadable DXF: {name}") from exc

        self.msp: Modelspace = self.doc.modelspace()

    # ----------------------------------------------

    def _text_paths(self, entity: DXFEntity) -> list[Polyline]:
        segments: list[Polyline] = []
        for path in text2path.make_paths_from_entity(entity):
            segments.extend(path_to_polylines(path, self.acc))
        return segments

    def text_path(self, mtext: MText) -> list[Polyline]:
        segments: list[Polyline] = []
        for txt in mtext_to_texts(mtext, self.doc):
            segments.extend(self._text_paths(txt))
        return segments

    # ----------------------------------------------

    def handle_entity(self, e: DXFEntity) -> list[Polyline]:
        e_type = e.dxftype()

        if self.debug:
            print(f"Processing: {e_type}")

        if e_type == "LINE":
            s, end = e.dxf.start, e.dxf.end
            return [[(s.x, s.y), (end.x, end.y)]]

        if e_type == "CIRCLE":
            return [circle_to_polyline(e, self.acc)]

        if e_type == "ELLIPSE":
            return [ellipse_to_polyline(e, self.acc)]

        if e_type == "ARC":
            # make_path respects extrusion; derive deflection from the chord length
            arc: Arc = e  # type: ignore[assignment]
            distance = sagitta_for_chord(arc.dxf.radius, self.acc)
            return entity_to_polylines(arc, distance)

        if e_type in ("LWPOLYLINE", "POLYLINE", "SPLINE"):
            # make_path handles bulges, closed flags, and splines
            return entity_to_polylines(e, self.acc)

        if e_type in ("SOLID", "TRACE", "3DFACE"):
            return entity_to_polylines(e, 0.01)

        if e_type == "POINT":
            return [point_entity(e, self.point_radius, self.acc)]

        if not self.text:
            return []

        if e_type == "MTEXT":
            return self.text_path(e)

        if e_type in ("TEXT", "ATTRIB"):
            return self._text_paths(e)

        return []

    # ----------------------------------------------

    def _expand(self, entities: Iterable[DXFEntity], depth: int = 0) -> Iterator[DXFEntity]:
        """Yield simple entities, resolving block references and dimensions
        in memory (the document itself is never modified)."""
        for e in entities:
            e_type = e.dxftype()

            if e_type == "INSERT":
                if depth >= MAX_INSERT_DEPTH:
                    logger.warning("Max INSERT depth reached, skipping block")
                    continue
                try:
                    yield from self._expand(e.virtual_entities(), depth + 1)
                    yield from self._expand(e.attribs, depth + 1)
                except Exception as exc:
                    logger.warning("Failed to expand INSERT: %s", exc)

            elif e_type == "DIMENSION":
                try:
                    yield from self._expand(e.virtual_entities(), depth + 1)
                except Exception as exc:
                    logger.warning("Failed to explode DIMENSION: %s", exc)

            else:
                yield e

    # ----------------------------------------------

    def read(self) -> list[Polyline]:
        segments: list[Polyline] = []

        for e in self._expand(self.msp):
            try:
                for seg in self.handle_entity(e):
                    if seg:
                        segments.append(seg)
            except Exception as exc:
                logger.warning("Skipping %s: %s", e.dxftype(), exc)

        return segments