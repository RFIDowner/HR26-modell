"""Bare loften (hull_solid) fra worktree: gyldighet, flater, knuter, tid."""
import sys, time
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
sys.path.insert(0, WT)
from hr26 import hull as H, params as P
from OCP.BRep import BRep_Tool
from OCP.GeomAdaptor import GeomAdaptor_Surface
from OCP.BRepCheck import BRepCheck_Analyzer
nst = int(sys.argv[1]) if len(sys.argv) > 1 else 40
t = time.time()
s = H.hull_solid(nst, 26)
print(f"loft+transom cut {time.time()-t:.1f}s valid={s.isValid()} vol={s.Volume()/1e9:.4f} m3 faces={len(s.Faces())}")
for f in s.Faces():
    srf = BRep_Tool.Surface_s(f.wrapped)
    try:
        bs = GeomAdaptor_Surface(srf).BSpline()
        print(f"  face {f.geomType():8s} area {f.Area()/1e6:8.3f} m2  uknots {bs.NbUKnots():4d} vknots {bs.NbVKnots():4d}  udeg {bs.UDegree()} vdeg {bs.VDegree()}")
    except Exception as e:
        print(f"  face {f.geomType():8s} area {f.Area()/1e6:8.3f} m2")
bb = s.BoundingBox()
print("bbox x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f" % (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
import cadquery as cq
s.exportBrep(r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/a2/loft_a2.brep")
