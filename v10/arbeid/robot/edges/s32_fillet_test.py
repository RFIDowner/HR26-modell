import sys, time
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges/repo")
import cadquery as cq
from hr26 import deckhouse as D, params as P, curves as C, hull as H
t0 = time.time()
def vol(w): return w.val().Volume()
# 1) coachroof with nudged wedge, then fillet the roof-face edges
z0 = min(C.sheer_z(x) for x in (P.STEP_X0, P.COACH_X1)) - 200.0
z1 = max(z for _, z in P.COACH_TOP) + 80.0
n = 60
stb = [(P.STEP_X0 + (P.COACH_X1 - P.STEP_X0) * i / n, 0.0) for i in range(n + 1)]
stb = [(x, D.coach_half_width(x)) for x, _ in stb]
prism = D._plan_prism_outline(stb, z0, z1, P.COACH_RAD)
roof = D._roof_body(P.STEP_X0 - 300.0, P.COACH_X1 + 300.0, D.roof_z, 1500.0, 2400.0, camber=P.COACH_ROOF_CAMBER)
base = prism.intersect(roof)
cr = base.cut(D._step_wedge().translate((-0.37, 0, 0)))
print("coachroof: removed by nudged wedge %.1f L" % ((vol(base) - vol(cr)) / 1e6))
top = cr.faces(">Z")
print(" top face edges:", len(top.edges().vals()))
for R in (25.0, 40.0):
    try:
        f = cr.faces(">Z").edges().fillet(R)
        print(f"  fillet R{R:.0f} on roof edges: ok={f.val().isValid()} dV={(vol(cr)-vol(f))/1e6:.2f} L  solids={len(f.val().Solids())}")
    except Exception as e:
        print(f"  fillet R{R:.0f} on roof edges FAILED: {type(e).__name__} {str(e)[:80]}")
# 2) coaming block top edges
cb = D.coaming_block()
try:
    f = cb.faces(">Z").edges().fillet(25.0)
    print(f"coaming top fillet R25: ok={f.val().isValid()} dV={(vol(cb)-vol(f))/1e6:.2f} L")
except Exception as e:
    print("coaming top fillet R25 FAILED:", type(e).__name__, str(e)[:80])
# 3) bare hull loft: fillet the sheer (deck-edge) edges
t1 = time.time()
hs = cq.Workplane("XY").newObject([H.hull_solid(40, 26)])
print("hull loft built %.0fs, faces %d, edges %d" % (time.time() - t1, len(hs.faces().vals()), len(hs.edges().vals())))
# sheer edges: edges whose midpoint is near the deck edge (|y| ~ deck half-breadth, z ~ sheer)
cand = []
for e in hs.edges().vals():
    p = e.positionAt(0.5)
    if 300 < p.x < 7600 and abs(abs(p.y) - C.deck_half_breadth(p.x)) < 15 and abs(p.z - C.sheer_z(p.x)) < 15:
        cand.append(e)
print(" sheer edges found:", len(cand))
for R in (25.0,):
    try:
        f = hs.newObject([hs.val().fillet(R, cand)]) if cand else None
        print(f"  hull sheer fillet R{R:.0f}: ok={f.val().isValid()} dV={(vol(hs)-vol(f))/1e6:.2f} L")
    except Exception as e:
        print(f"  hull sheer fillet R{R:.0f} FAILED: {type(e).__name__} {str(e)[:100]}")
print("total %.0fs" % (time.time() - t0))
