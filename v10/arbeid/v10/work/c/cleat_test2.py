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
for r in (6.0, 4.0):
    try:
        c = cq.Workplane("XZ").spline(pts, periodic=True).close().extrude(0.5 * W, both=True)
        out = c.faces(">Y or <Y").edges().fillet(r)
        print("fillet", r, "valid", out.val().isValid())
    except Exception as e:
        print("fillet", r, "FEIL", e)
# loft-variant: krympede profiler
def profile_pts(shrink, n=120):
    e = cq.Edge.makeSpline([cq.Vector(x, 0, z) for x, z in pts], periodic=True)
    P = np.array([[e.positionAt(t).x, e.positionAt(t).z] for t in np.linspace(0, 1, n, endpoint=False)])
    d = np.roll(P, -1, axis=0) - np.roll(P, 1, axis=0)
    nrm = np.c_[d[:, 1], -d[:, 0]]; nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    # inward = towards centroid
    c0 = P.mean(0)
    if np.mean(np.einsum("ij,ij->i", nrm, c0 - P)) < 0: nrm = -nrm
    return P + shrink * nrm
r = 10.0
ys = [-(0.5 * W - 0.05 * r), -(0.5 * W - 0.4 * r), -(0.5 * W - r), 0.0, 0.5 * W - r, 0.5 * W - 0.4 * r, 0.5 * W - 0.05 * r]
wires = []
for y in ys:
    u = max(0.0, abs(y) - (0.5 * W - r))
    s = r - math.sqrt(max(r * r - u * u, 0.0))
    Q = profile_pts(s)
    e = cq.Edge.makeSpline([cq.Vector(x, y, z) for x, z in Q], periodic=True)
    wires.append(cq.Wire.assembleEdges([e]))
sol = cq.Solid.makeLoft(wires, ruled=False)
print("loft valid", sol.isValid(), "V", sol.Volume())
sol.exportStl("parts/cleat_loft.stl", 0.06, 0.05, False, False)
deck = cq.Workplane("XY").box(400, 200, 50).translate((0, 0, -25 + 0.01))
u = deck.union(cq.Workplane("XY").newObject([sol]))
print("union solids", len(u.solids().vals()), u.val().isValid())
u.val().scale(1 / 30).exportStl("parts/cleat_union.stl", 0.01, 0.05, False, False)
F, cc = nm("parts/cleat_union.stl")
print("nm edges", len(F))
