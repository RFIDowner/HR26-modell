import sys, math, time
import numpy as np
sys.path.insert(0, ".")
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck")
import cadquery as cq
from hr26 import fittings as F

c = F._cleat(700.0, 228.0).val()
print("loft-klamp: faces", len(c.Faces()), "tri at 0.3 mm/0.05 rad:", end=" ")
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
def count(s, lin, ang):
    BRepMesh_IncrementalMesh(s.wrapped, lin, False, ang, True)
    return sum((BRep_Tool.Triangulation_s(f.wrapped, TopLoc_Location()) or type("x", (), {"NbTriangles": lambda self: 0})()).NbTriangles() for f in s.Faces())
print(count(c, 0.3, 0.05))
from OCP.GeomAdaptor import GeomAdaptor_Surface
for f in c.Faces():
    a = GeomAdaptor_Surface(BRep_Tool.Surface_s(f.wrapped))
    try: print("   face", f.geomType(), "knots", a.NbUKnots(), a.NbVKnots(), "deg", a.UDegree(), a.VDegree())
    except Exception: print("   face", f.geomType())
