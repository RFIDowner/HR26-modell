"""Part b with a fixed WC locker: below the ceiling as before, above it only
outboard of the opening edge + GAP (like the galley lockers and the mirror
cabinet), so no faces coincide with the opening/ceiling edge."""
import sys, time
WC = sys.argv[1]; BREP = sys.argv[2]
sys.path.insert(0, WC)
import numpy as np, cadquery as cq
from hr26 import params as P, interior as I, deckhouse as D, shell as S, build as B

_orig = I._wc_room
def _wc_room_fixed(z_low, z_high):
    t = 0.5 * P.INT_BH_T
    xa, xb = P.INT_BH_WC_FWD + t, P.INT_BH_WC_AFT - t
    zc = min(I.ceiling_ref(float(x))[1] for x in np.linspace(xa, xb, 25)) - 3.0 * I.GAP
    rest = _orig(z_low, z_high).cut(I._box(xa, xb, -I.BIG, -P.INT_WC_LOCKER_Y + 0.01, z_low - 1, I.BIG))  # drop old locker
    low = I._box(xa, xb, -I.BIG, -P.INT_WC_LOCKER_Y, z_low, zc)
    high = I._hull_band(xa, xb, lambda x: I.ceiling_ref(x)[0] + I.GAP, zc - 1.0, z_high, n=12).mirror("XZ")
    return rest.union(low).union(high)
I._wc_room = _wc_room_fixed

t0 = time.time()
w = cq.Workplane("XY").newObject([cq.Shape.importBrep(BREP)])
win_cut, win_keep = D.hull_windows()
w = S.hollow(w, keep=[D.cockpit_tub(P.HULL_WALL), win_keep, D.mast_post(), I.keep_block()])
void = I.cabin_void(with_opening=False)
out = w.cut(void)
sols = out.val().Solids()
print(f"[{time.time()-t0:5.1f}s] fixed WC locker: after cabin cut {len(sols)} solids, valid {out.val().isValid()}, "
      f"vol {sum(s.Volume() for s in sols)/P.SCALE**3/1000:.3f} cm3")
try:
    w2 = B.robust_cut(out, I.window_holes(), "aapne vinduer", strict=True)
    print("window holes ok:", len(w2.val().Solids()), "solids, valid", w2.val().isValid())
except Exception as e:
    print("window holes:", e)
