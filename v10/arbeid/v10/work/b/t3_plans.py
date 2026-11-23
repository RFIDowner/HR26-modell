import sys, math, time
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import numpy as np, cadquery as cq
from hr26 import hull as H
pl = np.array(H._stern_plans())
for r in pl[::2]:
    print("  z=%6.0f yt=%6.1f R=%6.0f a=%5.1f" % (r[0], r[1], r[2], math.degrees(r[3])))
t = time.time()
s = H._rounded_cutter().val()
bb = s.BoundingBox(); print("cutter %.1fs bbox x %.0f..%.0f y %.0f..%.0f valid %s" % (time.time()-t, bb.xmin, bb.xmax, bb.ymin, bb.ymax, s.isValid()))
for p in [(7900, 0, 0), (7900, 0, 500), (7850, 500, 400), (7700, 0, 0), (8000, 800, 0)]:
    print(p, s.isInside(cq.Vector(*p)))
