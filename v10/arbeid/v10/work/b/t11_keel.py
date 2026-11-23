import sys, time
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import cadquery as cq
from OCP.BOPAlgo import BOPAlgo_ArgumentAnalyzer
from hr26 import appendages as A, hull as H
t = time.time()
k = A.keel().val()
an = BOPAlgo_ArgumentAnalyzer(); an.SetShape1(k.wrapped); an.Perform()
bb = k.BoundingBox()
print("keel %.1fs valid %s faulty %s faces %d bbox x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f" % (time.time()-t, k.isValid(), an.HasFaulty(), len(k.Faces()), bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
hs = cq.Workplane("XY").newObject([H.hull_solid(40, 26)])
u = hs.union(cq.Workplane("XY").newObject([k]))
print("union solids", len(u.val().Solids()), "valid", u.val().isValid())
k.scale(1/30).exportStl(WT + "/../../v10/work/b/t11_keel.stl", 0.005, 0.05, False, False)
