import sys, time
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import numpy as np, cadquery as cq
from hr26 import hull as H, params as P
s = H.rubbing_strake().val()
for f in s.Faces():
    bb = f.BoundingBox(); print("strake face", f.geomType(), "area %.4g" % f.Area(), "x %.0f..%.0f y %.0f..%.0f" % (bb.xmin, bb.xmax, bb.ymin, bb.ymax))
from OCP.BOPAlgo import BOPAlgo_ArgumentAnalyzer
an = BOPAlgo_ArgumentAnalyzer(); an.SetShape1(s.wrapped)
try:
    an.SelfInterMode = True
except Exception: pass
an.Perform(); print("strake self-check has faulty:", an.HasFaulty())
hs = cq.Workplane("XY").newObject([H.hull_solid(40, 26)])
u = hs.union(cq.Workplane("XY").newObject([s]))
for so in u.val().Solids():
    bb = so.BoundingBox(); print("solid faces %d  x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f" % (len(so.Faces()), bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
