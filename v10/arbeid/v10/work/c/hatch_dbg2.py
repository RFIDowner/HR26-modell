import sys, math
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck")
import cadquery as cq
from hr26 import deckhouse as D, params as P
from OCP.BOPAlgo import BOPAlgo_ArgumentAnalyzer
h = D.hatches().solids().vals()[1]
def st_v1():
    bury = 35.0
    x_s = P.STEP_X0 - bury / math.tan(math.radians(P.COACH_FRONT_ANGLE)) + 4.0
    xm = P.STEP_X0 + P.COACH_FRONT_R
    xs = D._quarter_sections(x_s, xm, 24)
    xa = P.COACH_X1 - P.COACH_RAD
    n = max(2, int((xa - xm) / 160.0))
    xs += [xm + (xa - xm) * i / n for i in range(1, n + 1)]
    xs += [xa + P.COACH_RAD * math.sin(math.radians(a)) for a in (15, 30, 45, 60, 75)]
    return xs
def st_uniform(step):
    def f():
        bury = 35.0
        x_s = P.STEP_X0 - bury / math.tan(math.radians(P.COACH_FRONT_ANGLE)) + 4.0
        xm = P.STEP_X0 + P.COACH_FRONT_R
        xa = P.COACH_X1 - P.COACH_RAD
        xs = D._quarter_sections(x_s, xm, 24) + D._even_sections(xm, xa, step)
        xs += [xa + P.COACH_RAD * math.sin(math.radians(a)) for a in (15, 30, 45, 60, 75)]
        return xs
    return f
variants = {"v2 (90/45)": D._coach_stations, "v1 (160)": st_v1, "uni 120": st_uniform(120.0), "uni 100": st_uniform(100.0)}
for name, fn in variants.items():
    D._coach_stations = fn
    c = D.coachroof()
    an = BOPAlgo_ArgumentAnalyzer(); an.SetShape1(c.val().wrapped); an.SelfInterMode = True
    an.Perform()
    u = c.union(cq.Workplane("XY").newObject([h]))
    print(f"{name:12s} n={len(fn())} dV={u.val().Volume() - c.val().Volume():12.0f} solids={len(u.solids().vals())} selfinter_faults={an.HasFaulty()}", flush=True)
