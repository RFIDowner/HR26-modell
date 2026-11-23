"""Part b diagnostics: hollow + cabin_void cut done by hand; report every solid (volume, bbox)."""
import sys, time, os
WC = sys.argv[1]; BREP = sys.argv[2]
sys.path.insert(0, WC)
import numpy as np, cadquery as cq
from hr26 import params as P, interior as I, deckhouse as D, shell as S
t0 = time.time()
w = cq.Workplane("XY").newObject([cq.Shape.importBrep(BREP)])
win_cut, win_keep = D.hull_windows()
keep = [D.cockpit_tub(P.HULL_WALL), win_keep, D.mast_post(), I.keep_block()]
w = S.hollow(w, keep=keep)
print(f"[{time.time()-t0:5.1f}s] hollowed: solids {len(w.val().Solids())} valid {w.val().isValid()}", flush=True)
void = I.cabin_void(with_opening=False)
print(f"[{time.time()-t0:5.1f}s] void: solids {len(void.val().Solids())} valid {void.val().isValid()}", flush=True)
out = w.cut(void)
sols = out.val().Solids()
print(f"[{time.time()-t0:5.1f}s] after cut: {len(sols)} solids, valid {out.val().isValid()}")
for s in sorted(sols, key=lambda s: -s.Volume()):
    bb = s.BoundingBox()
    print(f"  vol {s.Volume()/P.SCALE**3/1000:9.4f} cm3 model  bbox x {bb.xmin:7.1f}..{bb.xmax:7.1f} y {bb.ymin:7.1f}..{bb.ymax:7.1f} z {bb.zmin:7.1f}..{bb.zmax:7.1f}  valid {s.isValid()}")
    if s.Volume() < 0.5 * max(t.Volume() for t in sols):
        s.exportBrep(os.path.join(os.path.dirname(BREP), "segk_piece.brep"))
