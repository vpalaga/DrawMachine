from __future__ import annotations

import math

import numpy as np

Point = tuple[float, float]
Polyline = list[Point]


def travel_distance(polylines: list[Polyline], start: Point = (0.0, 0.0)) -> float:
    """Total pen-up distance: start -> first polyline, and end of each polyline
    -> start of the next one."""
    total = 0.0
    pos = start
    for pl in polylines:
        total += math.dist(pos, pl[0])
        pos = pl[-1]
    return total


def is_closed(polyline: Polyline, tol: float = 1e-6) -> bool:
    return len(polyline) > 2 and math.dist(polyline[0], polyline[-1]) <= tol


def _rotate_closed(polyline: Polyline, pos: np.ndarray) -> Polyline:
    """Re-start a closed loop at the vertex closest to `pos`."""
    pts = np.asarray(polyline[:-1], dtype=float)
    k = int(np.argmin(np.hypot(pts[:, 0] - pos[0], pts[:, 1] - pos[1])))
    if k == 0:
        return polyline
    return polyline[k:-1] + polyline[:k] + [polyline[k]]


def optimize_order(
    polylines: list[Polyline],
    start: Point = (0.0, 0.0),
    tol: float = 1e-6,
) -> list[Polyline]:
    """Reorder polylines to reduce pen-up travel (greedy nearest neighbour).

    At each step the pen goes to the closest unvisited polyline end point:
      * open polylines may be drawn in reverse if their last point is closer,
      * closed loops are re-started at their vertex closest to the pen.

    Polylines that touch the pen's current position end up directly after one
    another, so the caller can skip the pen lift between them.
    Vectorised with numpy, so thousands of polylines are no problem.
    """
    items = [pl for pl in polylines if pl]
    n = len(items)
    if n == 0:
        return []

    starts = np.array([pl[0] for pl in items], dtype=float)
    ends = np.array([pl[-1] for pl in items], dtype=float)
    closed = [is_closed(pl, tol) for pl in items]

    visited = np.zeros(n, dtype=bool)
    pos = np.array(start, dtype=float)
    ordered: list[Polyline] = []

    for _ in range(n):
        d_start = np.hypot(starts[:, 0] - pos[0], starts[:, 1] - pos[1])
        d_end = np.hypot(ends[:, 0] - pos[0], ends[:, 1] - pos[1])
        d_start[visited] = np.inf
        d_end[visited] = np.inf

        i_start = int(np.argmin(d_start))
        i_end = int(np.argmin(d_end))

        if d_start[i_start] <= d_end[i_end]:
            idx, reverse = i_start, False
        else:
            idx, reverse = i_end, True

        visited[idx] = True
        pl = items[idx]

        if closed[idx]:
            pl = _rotate_closed(pl, pos)
        elif reverse:
            pl = pl[::-1]

        ordered.append(pl)
        pos = np.array(pl[-1], dtype=float)

    return ordered
