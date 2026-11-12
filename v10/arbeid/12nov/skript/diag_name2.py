import sys, time
sys.path.insert(0, sys.argv[1])
import cadquery as cq
from hr26 import build as B, hull as H, appendages as A, deckhouse as D, fittings as F
nm = F.transom_name()
w = cq.Workplane("XY").newObject([H.hull_solid(40, 26)])
steps = ((A.keel, "kjol"), (H.rubbing_strake, "fenderlist"), (D.coachroof, "ruff"), (D.hatches, "luker"),
         (D.vents, "ventiler"), (D.coaming_block, "karm"), (D.sprayhood, "sprayhood"))
for f, n in steps:
    w = B.robust_union(w, f(), n)
    v0 = B._volume(w)
    c = w.union(nm)
    print(f"etter {n:10s}: navn dV={B._volume(c)-v0:.4e}", flush=True)
