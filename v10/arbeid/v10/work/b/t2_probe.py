import sys
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import cadquery as cq
from hr26 import hull as H
s = H._rounded_cutter().val()
bb = s.BoundingBox(); print("bbox", round(bb.xmin), round(bb.xmax), round(bb.ymin), round(bb.ymax), round(bb.zmin), round(bb.zmax))
for p in [(7900, 0, 0), (8300, 0, 0), (7900, 0, 500), (7850, 500, 400), (7700, 0, 0), (8350, 1300, 0), (8000, 800, 0)]:
    print(p, s.isInside(cq.Vector(*p)))
for f in s.Faces():
    c = f.Center(); print(" face", f.geomType(), "area %.3g" % f.Area(), "center (%.0f %.0f %.0f)" % (c.x, c.y, c.z))
# one wire
pl = H._stern_plans()
z, yt, R, a = [p for p in pl if abs(p[0]) < 1][0]
w = H._cutter_wire(z, yt, R, a)
for e in w.Edges():
    print(" edge", e.geomType(), "start", [round(v) for v in e.startPoint().toTuple()], "end", [round(v) for v in e.endPoint().toTuple()])
f = cq.Face.makeFromWires(w); print("wire face area %.4g" % f.Area())
