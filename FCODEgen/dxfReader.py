from ezdxf.addons import text2path

from ezdxf.lldxf.const import (
    MTEXT_TOP_LEFT, MTEXT_TOP_CENTER, MTEXT_TOP_RIGHT,
    MTEXT_MIDDLE_LEFT, MTEXT_MIDDLE_CENTER, MTEXT_MIDDLE_RIGHT,
    MTEXT_BOTTOM_LEFT, MTEXT_BOTTOM_CENTER, MTEXT_BOTTOM_RIGHT,
)
from ezdxf.enums import TextEntityAlignment
import ezdxf

import math


def gen_circle(center:tuple[float, float], r:float, segments:int):
    pts = []
    c_x, c_y = center[0], center[1]

    for i in range(segments):
        theta = 2 * math.pi * i / segments
        x = c_x + r * math.cos(theta)
        y = c_y + r * math.sin(theta)
        pts.append((x, y))
    pts.append(pts[0])  # close loop
    return pts

def mtext_to_text(mtext, msp):
    lines = mtext.plain_text().split("\n")
    x0, y0, _ = mtext.dxf.insert
    height = mtext.dxf.char_height
    rot = math.radians(mtext.dxf.rotation)

    attach = mtext.dxf.attachment_point

    # Map MTEXT attachment to a TEXT alignment
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

    text_align = attach_map.get(attach, TextEntityAlignment.LEFT)

    texts = []
    dy = height

    for i, line in enumerate(lines):
        # vertical offset for this line (downwards)
        offset_y = -i * dy

        # rotate offsets
        dx_rot = offset_y * math.sin(rot)
        dy_rot = offset_y * math.cos(rot)

        t = msp.add_text(line, dxfattribs={"height": height})
        t.set_placement(
            (x0 + dx_rot, y0 + dy_rot),
            align=text_align,
        )
        texts.append(t)

    return texts

def circle_to_polyline(circle, line_len:float):
    """
    Approximate a CIRCLE entity as a polyline (list of points).
    segments: how many line segments to use (more = smoother)
    """

    center = circle.dxf.center
    r = circle.dxf.radius

    segments = round(((2*r*math.pi)/line_len))
    return gen_circle((center.x, center.y), r, segments)

def ellipse_to_polyline(ellipse, line_len: float):
    """
    Approximate an ELLIPSE entity with straight segments.
    Returns list of (x, y) for the approximate polyline (closed if full ellipse).
    """
    center = ellipse.dxf.center
    major = ellipse.dxf.major_axis
    ratio = ellipse.dxf.ratio
    start = ellipse.dxf.start_param
    end = ellipse.dxf.end_param

    # approximate circumference
    a = major.magnitude
    b = a * ratio
    # Ramanujan ellipse circumference approximation:
    approx_circ = math.pi * (3*(a + b) - math.sqrt((3*a + b)*(a + 3*b)))

    # decide number of segments
    segments = max(4, round(approx_circ / line_len))

    # generate parameter values
    params = [start + (end - start) * i / segments for i in range(segments + 1)]

    # get points
    pts = []
    for v in ellipse.vertices(params):
        pts.append((v.x, v.y))

    return pts

from ezdxf.path import make_path

def solid_to_edges(entity):
    """
    Convert a SOLID/TRACE/3DFACE into a sequence of 2D points
    that represent the edges of the face.
    """
    path = make_path(entity)  # supported including SOLID, TRACE, 3DFACE
    pts = [(p.x, p.y) for p in path.flattening(distance=0.01)]
    return pts

def generate_hatch_lines(shape_pts, spacing):
    """
    Returns a list of hatch lines (each line is a pair of points)
    spaced apart vertically by `spacing`.
    shape_pts is a list of (x, y) defining a closed polygon.
    """
    # 1) compute min/max y
    ys = [pt[1] for pt in shape_pts]
    y_min, y_max = min(ys), max(ys)

    hatch_lines = []
    y = y_min
    while y <= y_max:
        # line from (x_min, y) to (x_max, y)
        xs = [pt[0] for pt in shape_pts]
        x_min, x_max = min(xs), max(xs)

        hatch_lines.append((x_min, y))
        hatch_lines.append((x_max, y))

        y += spacing

    return hatch_lines

def point(point, radius:float, line_len:float):

    center = point.dxf.location
    segments = round(((2 * radius * math.pi) / line_len))

    return gen_circle((center[0], center[1]), radius, segments=segments)

class Reader:
    def __init__(self, name:str, acc=0.001):
        self.name = name
        self.acc = acc

        try:
            self.doc = ezdxf.readfile(name)
            self.msp = self.doc.modelspace()

        except IOError:
            raise FileNotFoundError("filename: {" + name + "} is invalid")

        except ezdxf.DXFStructureError:
            raise ValueError("file: {" + name + "} is unreadable")

    def text_path(self, mtext):
        texts = mtext_to_text(mtext, self.msp)
        all_pts = []

        for txt in texts:
            paths = text2path.make_paths_from_entity(txt)

            for path in paths:
                pts = [
                    (
                        p[0],
                        p[1],
                    )
                    for p in path.flattening(distance=self.acc)
                ]

                # Optional: close the path
                # if pts:
                #     pts.append(pts[0])

                all_pts += pts

        return all_pts

    # helper function
    def print_entity(self, e) -> list[tuple[float,float]]:
        #print(e.dxftype() + " on layer: %s" % e.dxf.layer)
        segment = []
        e_type = e.dxftype()

        if e_type == "LINE":
            s_x, s_y = e.dxf.start[0], e.dxf.start[1]
            e_x, e_y = e.dxf.end[0],   e.dxf.end[1]

            #print("start point: %s" % e.dxf.start)
            #print("end point: %s\n" % e.dxf.end)

            #self.vis.line((s_x, s_y), (e_x, e_y))
            segment = [(s_x, s_y), (e_x, e_y)]

        elif e_type == "MTEXT":
            segment = self.text_path(e)

        elif e_type == "DIMENSION":
            print("DIMENSION")
            segment = []
            # add dimention points later

        elif e_type == "CIRCLE":
            segment = circle_to_polyline(e, line_len=self.acc)
        elif e_type == "ELLIPSE":
            segment = ellipse_to_polyline(e, line_len=self.acc)
        elif e_type == "SOLID":
            segment = solid_to_edges(e)
            """use only the edges"""
            #print(segment)
            #segment += generate_hatch_lines(segment, 0.1)
            #print(segment)
        elif e_type == "POINT":
            segment = point(e, 0.3, line_len=self.acc)

        elif e_type == "TEXT":
            print("text: " + e.dxf.text)

        else:
            print("p" + e_type)

        return segment

    def read(self):
        segments = []

        #explode dimentions into objects
        for dim in self.msp.query("DIMENSION"):
            parts = dim.explode()
            for e in parts:
                if e.dxftype() == "ARC" and False:
                    pts = [(p.x, p.y) for p in e.flattening(distance=0.1)]
                    #add_poly_as_lines(msp, pts)

                if e.dxftype() == "LINE":
                    self.msp.add_line(e.dxf.start, e.dxf.end)
                else:
                    pass
                    # store TEXT, MTEXT, or other entities as needed
                    #handle_entity(e)

        # iterate over all entities in modelspace
        for e in self.msp:
            segment = self.print_entity(e)

            if len(segment) > 0: # check for empy segments
                segments.append(segment)

        #self.vis.show()
        return segments

    
if __name__ == "__main__":
    Reader("Drawing 2.dxf").read()
