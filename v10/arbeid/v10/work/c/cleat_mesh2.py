import sys, math
import numpy as np
sys.path.insert(0, ".")
import cadquery as cq
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from nm_where import nm
def count(s, lin=0.3, ang=0.05):
    BRepMesh_IncrementalMesh(s.wrapped, lin, False, ang, True)
    n = 0
    for f in s.Faces():
        t = BRep_Tool.Triangulation_s(f.wrapped, TopLoc_Location())
        n += t.NbTriangles() if t is not None else 0
    return n
L, W, H = 180.0, 45.0, 60.0
a = 0.5 * L
half = [(0.0, -25.0), (0.18 * L, -25.0), (0.22 * L, -10.0), (0.22 * L, 0.13 * H),
        (0.29 * L, 0.3 * H), (0.39 * L, 0.45 * H), (0.48 * L, 0.6 * H), (a, 0.77 * H),
        (0.49 * L, 0.93 * H), (0.42 * L, H), (0.22 * L, 1.01 * H), (0.0, 1.02 * H)]
prof = half + [(-px, pz) for (px, pz) in reversed(half[1:-1])]
P0 = np.array(prof + [prof[0]])
ch = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P0, axis=0).T))]); par = list(ch / ch[-1])
def loft(ks, fixed):
    r = 9.0; cz, hx, hz = 0.5 * (H - 25.0), a, 0.5 * (H + 25.0); e = 0.5 * W - r
    wires = []
    for k in ks:
        yy = math.copysign(e + abs(k) * r, k) if k else 0.0
        if k and abs(k) < 1e-9: yy = 0.0
        u = max(0.0, abs(yy) - e); s = r - math.sqrt(max(r * r - u * u, 0.0))
        sx, sz = (hx - s) / hx, (hz - s) / hz
        vs = [cq.Vector(px * sx, yy, cz + (pz - cz) * sz) for px, pz in prof]
        sp = cq.Edge.makeSpline(vs, periodic=True, parameters=par if fixed else None)
        wires.append(cq.Wire.assembleEdges([sp]))
    return cq.Solid.makeLoft(wires, ruled=False)
def test(name, s):
    deck = cq.Workplane("XY").box(400, 200, 50).translate((0, 0, -25 + 0.01))
    u = deck.union(cq.Workplane("XY").newObject([s]))
    u.val().scale(1 / 30).exportStl("parts/cleat_union.stl", 0.01, 0.05, False, False)
    F, cc = nm("parts/cleat_union.stl")
    print(f"{name:22s} valid={s.isValid()} tri={count(s)} union_solids={len(u.solids().vals())} nm={len(F)} V={s.Volume():.0f}")
    return s
test("loft7 egne parametre", loft([-0.95, -0.6, -1e-12, 0.0, 1e-12, 0.6, 0.95], False)) if False else None
k7 = [-1.95, -1.6, -1.0, 0.0, 1.0, 1.6, 1.95]
def loft2(ks, fixed):
    r = 9.0; cz, hx, hz = 0.5 * (H - 25.0), a, 0.5 * (H + 25.0); e = 0.5 * W - r
    wires = []
    for yy in ks:
        u = max(0.0, abs(yy) - e); s = r - math.sqrt(max(r * r - u * u, 0.0))
        sx, sz = (hx - s) / hx, (hz - s) / hz
        vs = [cq.Vector(px * sx, yy, cz + (pz - cz) * sz) for px, pz in prof]
        sp = cq.Edge.makeSpline(vs, periodic=True, parameters=par if fixed else None)
        wires.append(cq.Wire.assembleEdges([sp]))
    return cq.Solid.makeLoft(wires, ruled=False)
e = 0.5 * W - 9.0
y7 = [-(e + 8.55), -(e + 5.4), -e, 0.0, e, e + 5.4, e + 8.55]
y5 = [-(e + 8.55), -e, 0.0, e, e + 8.55]
test("loft7 egne param", loft2(y7, False))
test("loft7 felles param", loft2(y7, True))
test("loft5 felles param", loft2(y5, True))
ext = cq.Workplane("XZ").spline(prof, periodic=True).close().extrude(0.5 * W, both=True).faces(">Y or <Y").edges().fillet(4.0)
test("ekstrudert R4", ext.val())
