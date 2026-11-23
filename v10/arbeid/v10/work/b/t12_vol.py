import sys
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import cadquery as cq
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from hr26 import hull as H, fittings as F, build as B
def ve(s):
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, p, 1e-6, False); return p.Mass()
c = H._rounded_cutter().val()
print("cutter plain %.6g adaptive %.6g" % (c.Volume(), ve(c)))
hs = H.hull_solid(40, 26)
print("hull plain %.6g adaptive %.6g" % (hs.Volume(), ve(hs)))
w = cq.Workplane("XY").newObject([hs])
name = F.transom_name()
u = w.union(name)
print("with name: solids %d plain %.6g adaptive %.6g (name vol %.4g)" % (len(u.val().Solids()), u.val().Volume(), ve(u.val()), name.val().Volume()))
st = H.rubbing_strake()
u2 = u.union(st)
print("with strake: solids %d plain %.6g adaptive %.6g" % (len(u2.val().Solids()), u2.val().Volume(), ve(u2.val())))
