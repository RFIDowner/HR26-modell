"""CAD robustness test of the patched scratch repo: aft hull segment + transom cut, keel, keel+segment union, cradles."""
import sys, time
REP = sys.argv[1]
sys.path.insert(0, REP)
import numpy as np
import cadquery as cq
from hr26 import params as P, curves as C, hull as H, appendages as A, stand as ST
from OCP.BRepCheck import BRepCheck_Analyzer
def ok(s): return BRepCheck_Analyzer(s.wrapped).IsValid()
t0 = time.time()
xs = [x for x in C.stations(40) if x >= 5300.0] + list(H.STERN_STATIONS) + [P.LOA - 2.0]
xs = sorted(set(xs)); xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 3.0]
wires = [H._section_wire(x, 26) for x in xs]
loft = cq.Solid.makeLoft(wires, ruled=False)
print("aft loft valid", ok(loft), "vol m3 %.4f" % (loft.Volume() / 1e9), "%.0fs" % (time.time() - t0), flush=True)
cut = cq.Workplane("XY").newObject([loft]).cut(H.transom_cutter())
sol = cut.val().Solids()
print("aft segment after transom cut: solids", len(sol), "valid", all(ok(s) for s in sol), "vol %.4f" % (sum(s.Volume() for s in sol) / 1e9),
      "bbox z", round(cut.val().BoundingBox().zmin, 1), "%.0fs" % (time.time() - t0), flush=True)
k = A.keel().val()
bb = k.BoundingBox()
print("keel valid", ok(k), "vol %.4f" % (k.Volume() / 1e9), "bbox x %.0f..%.0f z %.0f..%.0f" % (bb.xmin, bb.xmax, bb.zmin, bb.zmax), flush=True)
kp = A._KeelProfile()
print("keel fillet ends: fwd x %.0f z %.0f / aft x %.0f z %.0f" % (kp.fwd[0, 0], kp.fwd[0, 1], kp.aft[0, 0], kp.aft[0, 1]))
xs2 = [x for x in np.linspace(2950, 6150, 14)]
seg = cq.Solid.makeLoft([H._section_wire(float(x), 26) for x in xs2], ruled=False)
u = cq.Workplane("XY").newObject([seg]).union(cq.Workplane("XY").newObject([k]))
us = u.val().Solids()
print("keel + hull segment (2950-6150) union: solids", len(us), "valid", all(ok(s) for s in us),
      "added m3 %.4f" % ((sum(s.Volume() for s in us) - seg.Volume()) / 1e9), "%.0fs" % (time.time() - t0), flush=True)
for x in P.STAND_STATIONS:
    cr = ST.cradle(x).val()
    inter = cq.Workplane("XY").newObject([cr]).intersect(cq.Workplane("XY").newObject([k]))
    iv = sum(s.Volume() for s in inter.val().Solids()) if inter.val().Solids() else 0.0
    gap = cr.distance(k) if hasattr(cr, "distance") else None
    print(f"cradle {x}: valid {ok(cr)} vol {cr.Volume()/1e9:.4f} m3, overlap with keel {iv/1e9:.6f} m3", flush=True)
print("done %.0fs" % (time.time() - t0))
