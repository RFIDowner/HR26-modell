"""Er det den klemte spissen av hjoernebaandet i baugen? Loft fra x0 og tell."""
import sys, time
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
sys.path.insert(0, WT)
import cadquery as cq
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from hr26 import hull as H, params as P, curves as C
x0 = float(sys.argv[1]); ang = float(sys.argv[2])
xs = [x for x in C.stations(40) if x0 < x < P.LOA - 4.0]
xs = sorted(set([x0] + xs + list(H.STERN_STATIONS) + [P.LOA - 2.0]))
t = time.time()
loft = cq.Solid.makeLoft([H._section_wire(x, 26) for x in xs], ruled=False)
s = loft.scale(1.0 / 30.0)
BRepMesh_IncrementalMesh(s.wrapped, 0.01, False, ang, True)
out = []
for f in s.Faces():
    tri = BRep_Tool.Triangulation_s(f.wrapped, TopLoc_Location())
    out.append((f.geomType()[:3], round(f.Area(), 1), 0 if tri is None else tri.NbTriangles()))
print(f"x0={x0} ang={ang}: {time.time()-t:.1f}s total {sum(o[2] for o in out)}  {out}", flush=True)
