"""Loft-varianter i baugen: teller trekanter per flate ved absolutt mesh."""
import sys, time
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
sys.path.insert(0, WT)
import numpy as np
import cadquery as cq
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from hr26 import hull as H, params as P, curves as C


def count(solid):
    s = solid.scale(1.0 / 30.0)
    BRepMesh_IncrementalMesh(s.wrapped, 0.01, False, 0.05, True)
    out = []
    for f in s.Faces():
        tri = BRep_Tool.Triangulation_s(f.wrapped, TopLoc_Location())
        out.append((f.geomType()[:3], round(f.Area() * 900 / 1e6, 3), 0 if tri is None else tri.NbTriangles()))
    return out


def run(tag, bow, nose, start=None, nst=40):
    H.BOW_STATIONS = bow
    P.BOW_NOSE_L = nose
    C._GEOM.clear()
    t = time.time()
    s = H.hull_solid(nst, 26)
    r = count(s)
    big = sorted(r, key=lambda v: -v[2])[:5]
    print(f"{tag:28s} valid={s.isValid()} {time.time()-t:4.1f}s total tri {sum(v[2] for v in r):8d}  top: {big}", flush=True)


for args in [("A: (2,6) nose15", (2.0, 6.0), 15.0),
             ("B: (4,) nose0", (4.0,), 1e-6),
             ("C: (6,) nose15", (6.0,), 15.0),
             ("D: (15,) nose15", (15.0,), 15.0)]:
    run(*args)
