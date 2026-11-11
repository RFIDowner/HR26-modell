import sys, math
import numpy as np
sys.path.insert(0, ".")
import cadquery as cq
from nm_where import nm
L, W, H = 180.0, 45.0, 60.0
a = 0.5 * L
half = [(0.0, -25.0), (0.18 * L, -25.0), (0.22 * L, -10.0), (0.22 * L, 0.13 * H),
        (0.29 * L, 0.3 * H), (0.39 * L, 0.45 * H), (0.48 * L, 0.6 * H), (a, 0.77 * H),
        (0.49 * L, 0.93 * H), (0.42 * L, H), (0.22 * L, 1.01 * H), (0.0, 1.02 * H)]
pts = half + [(-x, z) for (x, z) in reversed(half[1:-1])]
def scaled_loft(r=9.0):
    cz = 0.5 * (H - 25.0)
    hx, hz = a, 0.5 * (H + 25.0)
    ys = [-(0.5 * W - 0.05 * r), -(0.5 * W - 0.4 * r), -(0.5 * W - r), 0.0, 0.5 * W - r, 0.5 * W - 0.4 * r, 0.5 * W - 0.05 * r]
    wires = []
    for y in ys:
        u = max(0.0, abs(y) - (0.5 * W - r))
        s = r - math.sqrt(max(r * r - u * u, 0.0))
        sx, sz = (hx - s) / hx, (hz - s) / hz
        e = cq.Edge.makeSpline([cq.Vector(x * sx, y, cz + (z - cz) * sz) for x, z in pts], periodic=True)
        wires.append(cq.Wire.assembleEdges([e]))
    return cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=False)])
variants = {
    "fillet4": cq.Workplane("XZ").spline(pts, periodic=True).close().extrude(0.5 * W, both=True).faces(">Y or <Y").edges().fillet(4.0),
    "scaledloft": scaled_loft(),
}
for name, out in variants.items():
    print(name, "valid", out.val().isValid(), "V", round(out.val().Volume()))
    out.val().exportStl(f"parts/cleat_{name}.stl", 0.06, 0.05, False, False)
    deck = cq.Workplane("XY").box(400, 200, 50).translate((0, 0, -25 + 0.01))
    u = deck.union(out)
    u.val().scale(1 / 30).exportStl("parts/cleat_union.stl", 0.01, 0.05, False, False)
    F, cc = nm("parts/cleat_union.stl")
    print("   union solids", len(u.solids().vals()), u.val().isValid(), "nm edges", len(F))
