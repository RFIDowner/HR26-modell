import sys
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import cadquery as cq
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from hr26 import hull as H, fittings as F, appendages as A, params as P
def ve(s):
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, p, 1e-6, False); return p.Mass()
w = cq.Workplane("XY").newObject([H.hull_solid(40, 26)])
print("hull       plain %.6g adaptive %.6g" % (w.val().Volume(), ve(w.val())))
w = w.union(A.keel()); print("+keel      plain %.6g adaptive %.6g" % (w.val().Volume(), ve(w.val())))
st = H.rubbing_strake(); print("strake alone plain %.6g adaptive %.6g" % (st.val().Volume(), ve(st.val())))
w = w.union(st); print("+strake    plain %.6g adaptive %.6g" % (w.val().Volume(), ve(w.val())))
ad = F.additions()
w2 = w.union(ad); print("+fittings  plain %.6g adaptive %.6g solids %d" % (w2.val().Volume(), ve(w2.val()), len(w2.val().Solids())))
