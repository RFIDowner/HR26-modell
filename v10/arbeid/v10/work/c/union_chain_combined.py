import sys, time
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/c/applytest")
import cadquery as cq
from hr26 import deckhouse as D, fittings as F, hull as H, build as B
t = time.time()
w = cq.Workplane("XY").newObject([H.hull_solid(40, 26)])
for name, fn in (("ruff", D.coachroof), ("luker", D.hatches), ("ventiler", D.vents), ("karm", D.coaming_block),
                 ("sprayhood", D.sprayhood), ("beslag", F.additions)):
    part = fn()
    w = B.robust_union(w, part, name)
    print(f"{name:10s} ok  solids={len(w.solids().vals())}  {time.time()-t:.0f}s", flush=True)
for name, fn in (("cockpit", D.cockpit_cut), ("nedgang", D.companionway_cut), ("rigg", F.cuts)):
    w = B.robust_cut(w, fn(), name)
    print(f"{name:10s} kutt ok solids={len(w.solids().vals())}  {time.time()-t:.0f}s", flush=True)
print("gyldig", w.val().isValid())
