import sys, time
sys.path.insert(0, sys.argv[1])
import cadquery as cq
from hr26 import build as B, hull as H, fittings as F
t = time.time()
w = cq.Workplane("XY").newObject([H.hull_solid(40, 26)])
v0 = B._volume(w)
nm = F.transom_name()
vn = B._volume(nm)
print(f"bart skrog {time.time()-t:.0f}s V0={v0:.6e} V(navn)={vn:.4e}", flush=True)
for label, kw in (("standard", {}), ("clean=False", {"clean": False}), ("tol=0.01", {"tol": 0.01}),
                  ("tol=0.1", {"tol": 0.1}), ("glue", {"glue": True})):
    try:
        c = w.union(nm, **kw)
        print(f"{label:12s} valid={c.val().isValid()} solider={B._n_solids(c)} dV={B._volume(c)-v0:.4e}", flush=True)
    except Exception as e:
        print(label, "feil", e, flush=True)
