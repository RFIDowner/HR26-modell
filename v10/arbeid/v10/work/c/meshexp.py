import sys, time, math
import numpy as np
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck")
import cadquery as cq
from hr26 import deckhouse as D, params as P
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
def ntri(s, tol=2.0):
    t = time.time()
    BRepMesh_IncrementalMesh(s.wrapped, tol, False, 0.1, True)
    n = []
    for f in s.Faces():
        tri = BRep_Tool.Triangulation_s(f.wrapped, TopLoc_Location())
        n.append(tri.NbTriangles() if tri is not None else 0)
    return n, time.time() - t
orig_wire = D._hf_wire
def wire_noparam(x, half, z_bot):
    full = np.vstack([half[::-1] * [-1.0, 1.0], half[1:]])
    vs = [cq.Vector(x, float(y), float(z)) for y, z in full]
    top = cq.Edge.makeSpline(vs)
    a, b = vs[0], vs[-1]
    lb, la = cq.Vector(x, b.y, z_bot), cq.Vector(x, a.y, z_bot)
    return cq.Wire.assembleEdges([top, cq.Edge.makeLine(b, lb), cq.Edge.makeLine(lb, la), cq.Edge.makeLine(la, a)])
orig_st = D._coach_stations
def st_uniform():
    xs = orig_st()
    x0, x1 = xs[0], xs[-1]
    n = int((x1 - x0) / 60)
    return [x0 + (x1 - x0) * i / n for i in range(n + 1)]
mode = sys.argv[1]
if "noparam" in mode: D._hf_wire = wire_noparam
if "uniform" in mode: D._coach_stations = st_uniform
t = time.time(); c = D.coachroof().val(); tb = time.time() - t
print(mode, "build", round(tb, 1), "valid", c.isValid(), "V", round(c.Volume() / 1e9, 4), ntri(c))
