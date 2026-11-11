import sys
exec(open(r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b/t5_variants.py").read().split("wires = [")[0])
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
cut = H._rounded_cutter().val()
r = loft.cut(cut)
def vol_eps(s, eps):
    p = GProp_GProps(); err = BRepGProp.VolumeProperties_s(s.wrapped, p, eps, False); return p.Mass(), err
print("plain Volume %.6g" % r.Volume())
print("eps 1e-3 %.6g err %.3g" % vol_eps(r, 1e-3))
print("eps 1e-5 %.6g err %.3g" % vol_eps(r, 1e-5))
tf = [f for f in r.Faces() if f.BoundingBox().xmin > 7700][0]
from OCP.BRep import BRep_Tool
srf = BRep_Tool.Surface_s(tf.wrapped)
from OCP.GeomAdaptor import GeomAdaptor_Surface
ad = GeomAdaptor_Surface(srf)
print("transom face surface: udeg", ad.UDegree(), "vdeg", ad.VDegree(), "nb uknots", ad.NbUKnots(), "nb vknots", ad.NbVKnots(), "U", ad.FirstUParameter(), ad.LastUParameter(), "V", ad.FirstVParameter(), ad.LastVParameter())
