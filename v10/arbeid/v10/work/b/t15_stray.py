import sys
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import cadquery as cq
from hr26 import hull as H, appendages as A
w = cq.Workplane("XY").newObject([H.hull_solid(40, 26)]).union(A.keel())
for dx in (0.0, 0.37, -0.37):
    st = H.rubbing_strake()
    u = w.union(st.translate((dx, 0, 0)) if dx else st)
    print("dx", dx, "solids", len(u.val().Solids()))
    for so in u.val().Solids():
        bb = so.BoundingBox()
        if bb.xlen < 5000:
            print("   stray: faces %d x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f vol %.3g" % (len(so.Faces()), bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax, so.Volume()))
