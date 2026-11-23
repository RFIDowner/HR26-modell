import sys, time
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopTools import TopTools_ListOfShape
from hr26 import hull as H, curves as C, params as P
xs = C.stations(40)
xs = [x for x in xs if 6.0 < x < P.LOA - 4.0]
xs = sorted(set([4.0] + xs + list(H.STERN_STATIONS) + [P.LOA - 2.0]))
xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 8.0]
loft = cq.Solid.makeLoft([H._section_wire(x, 26) for x in xs], ruled=False)
cut = H._rounded_cutter().val()
print("loft vol %.6g cutter vol %.4g" % (loft.Volume(), cut.Volume()))
print("cutter analyzer valid:", BRepCheck_Analyzer(cut.wrapped).IsValid())
op = BRepAlgoAPI_Cut(loft.wrapped, cut.wrapped)
print("done", op.IsDone(), [m for m in dir(op) if "rror" in m or "arn" in m][:6])
r = cq.Shape.cast(op.Shape())
print("result vol %.6g, solids %d faces %d" % (r.Volume(), len(r.Solids()), len(r.Faces())))
# common: what is the intersection volume?
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
cm = cq.Shape.cast(BRepAlgoAPI_Common(loft.wrapped, cut.wrapped).Shape())
print("common vol %.6g" % cm.Volume())
# section curves between the cutter front face and the loft
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
sec = cq.Shape.cast(BRepAlgoAPI_Section(loft.wrapped, cut.wrapped).Shape())
print("section edges", len(sec.Edges()))
old = H._plain_cutter().val()
r0 = cq.Shape.cast(BRepAlgoAPI_Cut(loft.wrapped, old.wrapped).Shape())
print("old cut vol %.6g faces %d" % (r0.Volume(), len(r0.Faces())))
