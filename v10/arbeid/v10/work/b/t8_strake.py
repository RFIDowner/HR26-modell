import sys, time
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import numpy as np, cadquery as cq
from hr26 import hull as H, params as P
t = time.time()
pts, nrm = H._strake_path()
print("path pts", len(pts), "%.1fs" % (time.time() - t), "end", pts[-1].round(1), "start", pts[0].round(1))
d = np.diff(pts[:, :2], axis=0); a = np.degrees(np.arctan2(d[:, 1], d[:, 0])); k = (np.diff(a) + 180) % 360 - 180
i = np.argmax(np.abs(k)); print("max plan turn per 20mm step %.2f deg at %s" % (k[i], pts[i + 1].round(0)))
t = time.time()
s = H.rubbing_strake().val()
print("strake %.1fs valid %s faces %d vol %.4g" % (time.time() - t, s.isValid(), len(s.Faces()), s.Volume()))
bb = s.BoundingBox(); print("bbox", round(bb.xmin), round(bb.xmax), round(bb.ymin), round(bb.ymax), round(bb.zmin), round(bb.zmax))
s.scale(1/30).exportStl(WT + "/../../v10/work/b/t8_strake.stl", 0.005, 0.05, False, False)
t = time.time()
hs = cq.Workplane("XY").newObject([H.hull_solid(40, 26)])
u = hs.union(cq.Workplane("XY").newObject([s]))
print("union %.1fs solids %d valid %s" % (time.time() - t, len(u.val().Solids()), u.val().isValid()))
u.val().scale(1/30).exportStl(WT + "/../../v10/work/b/t8_hull_strake.stl", 0.01, 0.05, False, False)
