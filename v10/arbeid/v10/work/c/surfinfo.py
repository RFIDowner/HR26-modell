import sys, time
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck")
from hr26 import deckhouse as D
from OCP.BRep import BRep_Tool
from OCP.GeomAdaptor import GeomAdaptor_Surface
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
def info(wp, tag):
    s = wp.val()
    for i, f in enumerate(s.Faces()):
        surf = BRep_Tool.Surface_s(f.wrapped)
        a = GeomAdaptor_Surface(surf)
        try:
            print(tag, i, f.geomType(), "deg", a.UDegree(), a.VDegree(), "knots", a.NbUKnots(), a.NbVKnots(), "poles", a.NbUPoles(), a.NbVPoles(), "area", round(f.Area()/1e6, 3))
        except Exception as e:
            print(tag, i, f.geomType(), round(f.Area()/1e6, 3))
    for tol in (2.0, 0.5):
        t = time.time()
        m = BRepMesh_IncrementalMesh(s.wrapped, tol, False, 0.1, True)
        n = 0
        for f in s.Faces():
            loc = TopLoc_Location()
            tri = BRep_Tool.Triangulation_s(f.wrapped, loc)
            if tri is not None: n += tri.NbTriangles()
        print(tag, "abs tol", tol, "triangles", n, f"{time.time()-t:.1f}s")
t = time.time(); c = D.coachroof(); print("bygget", time.time()-t)
info(c, "ruff")
