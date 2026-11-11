import sys, time
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.TopTools import TopTools_ListOfShape
from hr26 import hull as H, curves as C, params as P
xs = C.stations(40)
xs = [x for x in xs if 6.0 < x < P.LOA - 4.0]
xs = sorted(set([4.0] + xs + list(H.STERN_STATIONS) + [P.LOA - 2.0]))
xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 8.0]
loft = cq.Solid.makeLoft([H._section_wire(x, 26) for x in xs], ruled=False)
LV = loft.Volume()
def report(name, cutter):
    cm = cq.Shape.cast(BRepAlgoAPI_Common(loft.wrapped, cutter.wrapped).Shape()).Volume()
    t = time.time()
    r = loft.cut(cutter)
    print(f"{name:28s} cutter vol {cutter.Volume():.4g}  common {cm/1e6:7.1f} L  loft-result {(LV - r.Volume())/1e6:7.1f} L  valid {r.isValid()}  {time.time()-t:.1f}s")
wires = [H._cutter_wire(z, yt, R, a) for (z, yt, R, a) in H._stern_plans()]
report("smooth", cq.Solid.makeLoft(wires, ruled=False))
report("ruled", cq.Solid.makeLoft(wires, ruled=True))
report("smooth fixed", cq.Solid.makeLoft(wires, ruled=False).fix())
report("old prism", H._plain_cutter().val())
# reversed wire orientation
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeWire
sm = cq.Solid.makeLoft(wires, ruled=False)
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
c = BRepClass3d_SolidClassifier(sm.wrapped); c.PerformInfinitePoint(1e-6); print("infinite point state (should be OUT=1):", c.State())
