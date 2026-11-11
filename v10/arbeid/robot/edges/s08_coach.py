import sys, time
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges/repo")
import cadquery as cq
from hr26 import deckhouse as D, params as P, curves as C
t = time.time()
print("cadquery", cq.__version__)
pl = cq.Plane.named("XZ"); print("XZ plane xDir", pl.xDir, "yDir", pl.yDir, "zDir", pl.zDir)
w = D._step_wedge()
bb = w.val().BoundingBox(); print("wedge bbox x", round(bb.xmin), round(bb.xmax), "y", round(bb.ymin), round(bb.ymax), "z", round(bb.zmin), round(bb.zmax), "vol", round(w.val().Volume()/1e9, 3), "m3")
z0 = min(C.sheer_z(x) for x in (P.STEP_X0, P.COACH_X1)) - 200.0
z1 = max(z for _, z in P.COACH_TOP) + 80.0
n = 60
stb = [(P.STEP_X0 + (P.COACH_X1 - P.STEP_X0) * i / n, 0.0) for i in range(n + 1)]
stb = [(x, D.coach_half_width(x)) for x, _ in stb]
prism = D._plan_prism_outline(stb, z0, z1, P.COACH_RAD)
roof = D._roof_body(P.STEP_X0 - 300.0, P.COACH_X1 + 300.0, D.roof_z, 1500.0, 2400.0, camber=P.COACH_ROOF_CAMBER)
a = prism.intersect(roof)
b = a.cut(w)
print("prism-roof vol", round(a.val().Volume()/1e9, 4), " after wedge cut", round(b.val().Volume()/1e9, 4), " isValid", b.val().isValid())
bb = b.val().BoundingBox(); print("coachroof bbox x", round(bb.xmin), round(bb.xmax), "z", round(bb.zmin), round(bb.zmax))
# what the wedge should remove: intersect
c = a.intersect(w)
print("prism-roof-wedge vol", round(c.val().Volume()/1e9, 4) if c.vals() else None)
# section of b at y=0 near the front: probe points
for x in (2205, 2230, 2260, 2300, 2330, 2360):
    zs = []
    for zz in range(1150, 1400, 5):
        if b.val().isInside(cq.Vector(x, 0, zz)):
            zs.append(zz)
    print(f" x={x}: solid z {min(zs) if zs else None}..{max(zs) if zs else None}")
print("time", round(time.time() - t, 1))
