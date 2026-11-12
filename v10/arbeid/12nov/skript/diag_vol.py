import sys, time
sys.path.insert(0, sys.argv[1])
import cadquery as cq
from hr26 import build as B, hull as H, appendages as A, deckhouse as D, fittings as F
t = time.time()
w = cq.Workplane("XY").newObject([H.hull_solid(40, 26)])
for f, n in ((A.keel, "kjol"), (H.rubbing_strake, "fenderlist"), (D.coachroof, "ruff"), (D.hatches, "luker"),
             (D.vents, "ventiler"), (D.coaming_block, "karm"), (D.sprayhood, "sprayhood")):
    w = B.robust_union(w, f(), n)
print(f"grunnlag {time.time()-t:.0f}s valid={w.val().isValid()}", flush=True)
v0 = B._volume(w); print(f"presist V0 {v0:.6e}  ({time.time()-t:.0f}s)", flush=True)
add = F.additions()
print("additions valid", add.val().isValid(), "solider", len(add.val().Solids()), flush=True)
va = B._volume(add); print(f"presist V(add) {va:.6e}", flush=True)
c = w.union(add)
print("union valid", c.val().isValid(), "solider", B._n_solids(c), flush=True)
v1 = B._volume(c); print(f"presist V1 {v1:.6e}  dV {v1-v0:.4e}  ({time.time()-t:.0f}s)", flush=True)
# hver for seg
for k, p in (("winches", F.winches()), ("cleats", F.cleats()), ("stemhead", F.stemhead()), ("navn", F.transom_name())):
    c = w.union(p)
    print(f"{k:9s} valid={c.val().isValid()} dV_presis={B._volume(c)-v0:.4e} V(del)={B._volume(p):.4e}", flush=True)
