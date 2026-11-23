import sys, time
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges/repo")
import cadquery as cq
from hr26 import deckhouse as D, params as P, curves as C
w = D._step_wedge()
print("wedge valid", w.val().isValid(), "inside(2300,0,1340)", w.val().isInside(cq.Vector(2300, 0, 1340)), "inside(2000,0,2000)", w.val().isInside(cq.Vector(2000, 0, 2000)))
a = D.coachroof()   # as built
z0 = min(C.sheer_z(x) for x in (P.STEP_X0, P.COACH_X1)) - 200.0
z1 = max(z for _, z in P.COACH_TOP) + 80.0
n = 60
stb = [(P.STEP_X0 + (P.COACH_X1 - P.STEP_X0) * i / n, 0.0) for i in range(n + 1)]
stb = [(x, D.coach_half_width(x)) for x, _ in stb]
prism = D._plan_prism_outline(stb, z0, z1, P.COACH_RAD)
print("prism valid", prism.val().isValid(), "vol", round(prism.val().Volume()/1e9, 4), "inside(2300,0,1300)", prism.val().isInside(cq.Vector(2300, 0, 1300)))
roof = D._roof_body(P.STEP_X0 - 300.0, P.COACH_X1 + 300.0, D.roof_z, 1500.0, 2400.0, camber=P.COACH_ROOF_CAMBER)
pr = prism.intersect(roof)
for dx in (0.0, 0.37, -0.37, 1.0, -1.0, 5.0):
    ww = w.translate((dx, 0, 0))
    c = pr.cut(ww)
    print(f" wedge shifted {dx:5.2f}: vol after cut {c.val().Volume()/1e9:.4f}  removed {(pr.val().Volume()-c.val().Volume())/1e6:9.1f} cm3(full)")
# alternative: cut the prism (before intersect with roof)
c2 = prism.cut(w).intersect(roof)
print(" cut prism first, then roof: removed", round((pr.val().Volume() - c2.val().Volume())/1e6, 1))
