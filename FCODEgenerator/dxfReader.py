import math
import ezdxf

from ezdxf.addons import text2path
from ezdxf.enums import TextEntityAlignment
from ezdxf.lldxf.const import (
    MTEXT_TOP_LEFT, MTEXT_TOP_CENTER, MTEXT_TOP_RIGHT,
    MTEXT_MIDDLE_LEFT, MTEXT_MIDDLE_CENTER, MTEXT_MIDDLE_RIGHT,
    MTEXT_BOTTOM_LEFT, MTEXT_BOTTOM_CENTER, MTEXT_BOTTOM_RIGHT,
)
from ezdxf.path import make_path


# --------------------------------------------------
# Geometry helpers
# --------------------------------------------------

def gen_circle(center: tuple[float, float], r: float, segments: int):
    segments = max(8, segments)
    pts = []
    cx, cy = center

    for i in range(segments):
        theta = 2 * math.pi * i / segments
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)
        pts.append((x, y))

    pts.append(pts[0])  # close loop
    return pts


def circle_to_polyline(circle, line_len: float):
    center = circle.dxf.center
    r = circle.dxf.radius
    segments = max(8, round((2 * math.pi * r) / line_len))
    return gen_circle((center.x, center.y), r, segments)


def ellipse_to_polyline(ellipse, line_len: float):
    center = ellipse.dxf.center
    major = ellipse.dxf.major_axis
    ratio = ellipse.dxf.ratio
    start = ellipse.dxf.start_param
    end = ellipse.dxf.end_param

    a = major.magnitude
    b = a * ratio

    approx_circ = math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))
    segments = max(8, round(approx_circ / line_len))

    angle = math.atan2(major.y, major.x)

    pts = []
    for i in range(segments + 1):
        t = start + (end - start) * i / segments

        x = a * math.cos(t)
        y = b * math.sin(t)

        xr = x * math.cos(angle) - y * math.sin(angle)
        yr = x * math.sin(angle) + y * math.cos(angle)

        pts.append((center.x + xr, center.y + yr))

    return pts


def solid_to_edges(entity, acc=0.01):
    path = make_path(entity)
    return [(p.x, p.y) for p in path.flattening(distance=acc)]


def generate_hatch_lines(shape_pts, spacing):
    ys = [p[1] for p in shape_pts]
    xs = [p[0] for p in shape_pts]

    y_min, y_max = min(ys), max(ys)
    x_min, x_max = min(xs), max(xs)

    lines = []
    y = y_min

    while y <= y_max:
        lines.append([(x_min, y), (x_max, y)])
        y += spacing

    return lines


def point_entity(entity, radius: float, line_len: float):
    center = entity.dxf.location
    segments = max(8, round((2 * math.pi * radius) / line_len))
    return gen_circle((center.x, center.y), radius, segments)


# --------------------------------------------------
# TEXT handling
# --------------------------------------------------

def mtext_to_text(mtext, msp):
    lines = mtext.plain_text().split("\n")
    x0, y0, _ = mtext.dxf.insert
    height = mtext.dxf.char_height
    rotation = mtext.dxf.rotation

    attach = mtext.dxf.attachment_point

    attach_map = {
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

    align = attach_map.get(attach, TextEntityAlignment.LEFT)

    texts = []
    dy = height

    rot_rad = math.radians(rotation)

    for i, line in enumerate(lines):
        offset = -i * dy

        dx = offset * math.sin(rot_rad)
        dy_rot = offset * math.cos(rot_rad)

        t = msp.add_text(line, dxfattribs={
            "height": height,
            "rotation": rotation,
        })

        t.set_placement((x0 + dx, y0 + dy_rot), align=align)
        texts.append(t)

    return texts


# --------------------------------------------------
# Reader
# --------------------------------------------------

class Reader:
    def __init__(self, name: str, acc=0.5, text=True, debug=False):
        self.name = name
        self.acc = max(1e-6, acc)
        self.text = text
        self.debug = debug

        try:
            self.doc = ezdxf.readfile(name)
            self.msp = self.doc.modelspace()
        except IOError:
            raise FileNotFoundError(f"Invalid file: {name}")
        except ezdxf.DXFStructureError:
            raise ValueError(f"Unreadable DXF: {name}")

    # ----------------------------------------------

    def text_path(self, mtext):
        texts = mtext_to_text(mtext, self.msp)
        segments = []

        for txt in texts:
            paths = text2path.make_paths_from_entity(txt)

            for path in paths:
                pts = [(p[0], p[1]) for p in path.flattening(distance=self.acc)]
                if pts:
                    segments.append(pts)

        return segments

    # ----------------------------------------------

    def handle_entity(self, e):
        e_type = e.dxftype()

        if self.debug:
            print(f"Processing: {e_type}")

        if e_type == "LINE":
            s = e.dxf.start
            e_ = e.dxf.end
            return [[(s.x, s.y), (e_.x, e_.y)]]

        elif e_type == "MTEXT" and self.text:
            return self.text_path(e)

        elif e_type == "CIRCLE":
            return [circle_to_polyline(e, self.acc)]

        elif e_type == "ELLIPSE":
            return [ellipse_to_polyline(e, self.acc)]

        elif e_type in ("SOLID", "TRACE", "3DFACE"):
            pts = solid_to_edges(e, self.acc)
            return [pts] if pts else []

        elif e_type == "POINT":
            return [point_entity(e, 0.3, self.acc)]

        elif e_type == "ARC":
            pts = [(p.x, p.y) for p in e.flattening(self.acc)]
            return [pts]

        elif e_type == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points()]
            return [pts]

        elif e_type == "TEXT" and self.text:
            paths = text2path.make_paths_from_entity(e)
            segments = []
            for path in paths:
                pts = [(p[0], p[1]) for p in path.flattening(distance=self.acc)]
                if pts:
                    segments.append(pts)
            return segments

        return []

    # ----------------------------------------------

    def explode_dimensions(self):
        for dim in self.msp.query("DIMENSION"):
            try:
                parts = dim.explode()
                for e in parts:
                    if e.dxftype() == "LINE":
                        self.msp.add_line(e.dxf.start, e.dxf.end)
            except Exception:
                if self.debug:
                    print("Failed to explode dimension")

    # ----------------------------------------------

    def read(self):
        self.explode_dimensions()

        segments = []

        for e in self.msp:
            segs = self.handle_entity(e)
            for s in segs:
                if s:
                    segments.append(s)

        return segments