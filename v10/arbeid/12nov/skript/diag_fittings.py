import sys, time
sys.path.insert(0, sys.argv[1])
import cadquery as cq
from hr26 import build as B, hull as H, appendages as A, deckhouse as D, fittings as F
t = time.time()
w = cq.Workplane("XY").newObject([H.hull_solid(40, 26)])
w = B.robust_union(w, A.keel(), "kjol")
w = B.robust_union(w, H.rubbing_strake(), "fenderlist")
w = B.robust_union(w, D.coachroof(), "ruff")
w = B.robust_union(w, D.hatches(), "luker")
w = B.robust_union(w, D.vents(), "ventiler")
w = B.robust_union(w, D.coaming_block(), "cockpitkarm")
w = B.robust_union(w, D.sprayhood(), "sprayhood")
print(f"grunnlag {time.time()-t:.0f}s, solider {B._n_solids(w)}, vol {w.val().Volume():.4e}", flush=True)
parts = {"winches": F.winches(), "cleats": F.cleats(), "stemhead": F.stemhead()}
nm = F.transom_name()
if nm is not None:
    parts["navn"] = nm
for k, p in parts.items():
    n_p = len(p.vals()) if p is not None else 0
    sols = sum(len(v.Solids()) for v in p.vals())
    cand = w.union(p)
    print(f"{k:10s} deler={n_p} solider_i_del={sols} -> etter union solider={B._n_solids(cand)} dV={cand.val().Volume()-w.val().Volume():.3e}", flush=True)
    for i, s in enumerate(p.val().Solids() if p is not None else []):
        c2 = w.union(cq.Workplane('XY').newObject([s]))
        bb = s.BoundingBox()
        print(f"   solid {i}: x {bb.xmin:.0f}-{bb.xmax:.0f} y {bb.ymin:.0f}-{bb.ymax:.0f} z {bb.zmin:.0f}-{bb.zmax:.0f} -> solider {B._n_solids(c2)} dV {c2.val().Volume()-w.val().Volume():.3e}", flush=True)
