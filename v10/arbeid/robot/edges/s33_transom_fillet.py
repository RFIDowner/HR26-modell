import sys, time
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges/repo")
import cadquery as cq
from hr26 import hull as H, curves as C, params as P
hs = cq.Workplane("XY").newObject([H.hull_solid(40, 26)])
faces = hs.faces().vals()
for f in faces:
    c = f.Center(); print(" face", f.geomType(), "center x %.0f y %.0f z %.0f area %.0f" % (c.x, c.y, c.z, f.Area()))
# transom face = the one with centre x > 7700
tf = [f for f in faces if f.Center().x > 7700]
edges = tf[0].Edges() if tf else []
print("transom face edges:", len(edges))
for R in (10.0, 20.0):
    try:
        s = hs.val().fillet(R, edges)
        print(f" transom edge fillet R{R:.0f}: valid={s.isValid()} dV={(hs.val().Volume()-s.Volume())/1e6:.2f} L")
    except Exception as e:
        print(f" transom edge fillet R{R:.0f} FAILED: {type(e).__name__} {str(e)[:80]}")
