import sys, math
import numpy as np
sys.path.insert(0, ".")
import cadquery as cq
from nm_where import nm
def cleat(L=180.0, W=45.0, H=60.0, r=10.0):
    a = 0.5 * L
    half = [(0.0, -25.0), (0.18 * L, -25.0), (0.22 * L, -10.0), (0.22 * L, 0.13 * H),
            (0.29 * L, 0.3 * H), (0.39 * L, 0.45 * H), (0.48 * L, 0.6 * H), (a, 0.77 * H),
            (0.49 * L, 0.93 * H), (0.42 * L, H), (0.22 * L, 1.01 * H), (0.0, 1.02 * H)]
    pts = half + [(-x, z) for (x, z) in reversed(half[1:-1])]
    prof = cq.Workplane("XZ").spline(pts, periodic=True).close()
    c = prof.extrude(0.5 * W, both=True)
    out = c.faces(">Y or <Y").edges().fillet(r)
    return c, out
c, out = cleat()
print("valid", out.val().isValid(), "faces", len(out.faces().vals()), "V", out.val().Volume())
out.val().exportStl("parts/cleat_single.stl", 0.002 * 30, 0.05, False, False)
deck = cq.Workplane("XY").box(400, 200, 50).translate((0, 0, -25 + 0.01))
u = deck.union(out)
print("union solids", len(u.solids().vals()), u.val().isValid())
u.val().scale(1/30).exportStl("parts/cleat_union.stl", 0.01, 0.05, False, False)
F, cc = nm("parts/cleat_union.stl")
print("nm edges", len(F))
