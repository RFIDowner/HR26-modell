import sys
exec(open(r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b/t5_variants.py").read().split("wires = [")[0])
cut = H._rounded_cutter().val()
r = loft.cut(cut)
print("faces", len(r.Faces()), [f.geomType() for f in r.Faces()])
for f in r.Faces():
    bb = f.BoundingBox(); print("  face area %.4g  x %.0f..%.0f  y %.0f..%.0f z %.0f..%.0f" % (f.Area(), bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
r.scale(1/30).exportStl(r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b/t6_cut.stl", 0.01, 0.05, False, False)
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
sec = cq.Shape.cast(BRepAlgoAPI_Section(loft.wrapped, cut.wrapped).Shape())
for e in sec.Edges():
    bb = e.BoundingBox(); print("  sec edge len %.0f x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f" % (e.Length(), bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
