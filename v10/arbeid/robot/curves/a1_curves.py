"""Step 1-2: evaluate every longitudinal curve of hr26.curves densely,
list slope discontinuities (kinks) and curvature."""
import sys, os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "repo"))
from hr26 import curves as C
from hr26 import params as P
from hr26 import deckhouse as D

np.set_printoptions(linewidth=200, suppress=True)

def kinks_pl(xk, yk, label, min_deg=0.0, top=None):
    """Kink angle at each knot of a piecewise linear function (xk, yk)."""
    xk = np.asarray(xk, float); yk = np.asarray(yk, float)
    s = np.diff(yk) / np.diff(xk)
    th = np.degrees(np.arctan(s))
    dth = np.diff(th)                      # at interior knots xk[1:-1]
    h = 0.5 * (np.diff(xk)[:-1] + np.diff(xk)[1:])
    kap = np.radians(dth) / h              # discrete curvature 1/mm
    rows = list(zip(xk[1:-1], dth, kap, s[:-1], s[1:]))
    return rows

# ---------------------------------------------------------------- knots
print("=== station grid _X:", C._X[:3], "...", C._X[-3:], len(C._X))
print("_SX", C._SX, "\n_SY", C._SY)

# station positions used in the 01_skrog.stl build (build_hull: n_stations=40)
xs = C.stations(40)
xs = [x for x in xs if 6.0 < x < P.LOA - 4.0]
xs = sorted(set([4.0] + xs + [7850.0, 7910.0] + [P.LOA - 2.0]))
xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 8.0]
XS = np.array(xs)
print("loft stations (%d):" % len(XS), np.round(XS, 0))
print("spacing:", np.round(np.diff(XS), 0))
np.save(os.path.join(HERE, "loft_stations.npy"), XS)

# ---------------------------------------------------------------- dense eval
x = np.arange(0.0, 7950.0 + 1e-9, 10.0)
F = {
    "deck_half_breadth": np.array([C.deck_half_breadth(v) for v in x]),
    "sheer_z": np.array([C.sheer_z(v) for v in x]),
    "strake_z": np.array([C.strake_z(v) for v in x]),
    "bottom_z": np.array([C.bottom_z(v) for v in x]),
    "fullness": np.array([C.fullness(v) for v in x]),
    "wl_half_breadth": np.array([C.wl_half_breadth(v) for v in x]),
    "deck_camber": np.array([C.deck_camber(v) for v in x]),
    "deck_z0": np.array([C.deck_z(v, 0.0) for v in x]),
}
np.savez(os.path.join(HERE, "dense.npz"), x=x, **F)

# value jumps (C0 breaks)
for k, y in F.items():
    d = np.abs(np.diff(y))
    i = np.argmax(d)
    print(f"{k:18s} max |dy| per 10 mm = {d[i]:.2f} at x={x[i]:.0f}-{x[i+1]:.0f}")

# exact C0 check at x = 7300 (switch between faired table and STERN_OUTLINE)
lo = float(np.interp(7300.0 - 1e-6, C._X, C._HB)); hi = C.deck_half_breadth(7300.0)
print(f"deck_half_breadth at 7300: faired table -> {lo:.2f}, STERN_OUTLINE -> {hi:.2f}, step {hi-lo:+.2f} mm")
print("faired _HB around 7300:", [(float(a), round(float(b), 1)) for a, b in zip(C._X, C._HB) if 7000 <= a <= 7650])

# ---------------------------------------------------------------- kink tables
def report(label, xk, yk, x0=None, x1=None, ntop=12):
    rows = kinks_pl(xk, yk, label)
    if x0 is not None:
        rows = [r for r in rows if x0 <= r[0] <= x1]
    a = np.array([abs(r[1]) for r in rows])
    print(f"\n--- {label}: {len(rows)} interior knots, |kink| mean {a.mean():.3f} deg, max {a.max():.3f} deg")
    # sign changes of curvature (wiggles)
    sg = np.sign([r[1] for r in rows if abs(r[1]) > 1e-4])
    print(f"    curvature sign changes: {int((np.diff(sg) != 0).sum())}")
    order = np.argsort(-a)[:ntop]
    for i in sorted(order):
        xk_, dth, kap, s0, s1 = rows[i]
        print(f"    x={xk_:7.1f}  kink {dth:+7.3f} deg   kappa {kap*1e3:+8.4f} 1/m   slope {s0:+.4f} -> {s1:+.4f}")
    return rows

# raw DECK_EDGE_Z table (measured)
dz = np.array(P.DECK_EDGE_Z)
report("DECK_EDGE_Z raw table (measured sheer)", dz[:, 0], dz[:, 1], ntop=20)
# as used: faired 150 mm grid
report("sheer_z as used (_ZS on 150 mm grid)", C._X, C._ZS, ntop=12)
# strake
report("strake_z as used (_ZK)", C._X, C._ZK, ntop=10)
# raw strake column from CSV
raw = np.genfromtxt(os.path.join(HERE, "repo", "data", "hull_stations.csv"), delimiter=",", names=True)
report("strake_z_mm CSV column (before _fair)", raw["x_from_bow_mm"], raw["strake_z_mm"], ntop=10)
# deck half-breadth as used: table (x < 7300) + STERN_OUTLINE
xk = np.concatenate([C._X[C._X < 7300.0], C._SX])
yk = np.array([C.deck_half_breadth(v) for v in xk])
report("deck_half_breadth as used (_HB + STERN_OUTLINE)", xk, yk, ntop=25)
report("deck_half_breadth CSV column (before _fair)", raw["x_from_bow_mm"], raw["deck_half_breadth_mm"], ntop=12)
dh = np.genfromtxt(os.path.join(HERE, "repo", "data", "deck_halfbreadth.csv"), delimiter=",", names=True)
report("deck_halfbreadth.csv RAW trace (100.6 mm)", dh["x_from_bow_mm"], dh["half_breadth_mm"], ntop=12)
# fullness and waterplane (in x)
fk = np.array(P.SECTION_FULLNESS);
r = kinks_pl(fk[:, 0] * P.LOA, fk[:, 1], "")
print("\n--- SECTION_FULLNESS knots (x mm, d(m)/dx jump per m):")
for (xk_, dth, kap, s0, s1) in r:
    print(f"    x={xk_:7.1f}  dm/dx {s0*1000:+.4f} -> {s1*1000:+.4f} per m  (jump {1000*(s1-s0):+.4f}/m)")
wk = np.array(P.WATERPLANE)
xw = P.LWL_FWD + wk[:, 0] * P.LWL; yw = C._BW_MAX * wk[:, 1]
report("wl_half_breadth (WATERPLANE x _BW_MAX)", xw, yw, ntop=14)
print("    _BW_MAX =", C._BW_MAX)
# camber kink
hb = F["deck_half_breadth"]; cr = np.where(np.diff(np.sign(hb - 900.0)) != 0)[0]
print("\ndeck_camber kinks (hb crosses 900):", x[cr])
# bottom
report("bottom_z as used (_ZB, 8 passes)", C._X[C._X >= P.LWL_FWD], C._ZB[C._X >= P.LWL_FWD], ntop=8)

# deckhouse tables
ct = np.array(P.COACH_TOP); report("COACH_TOP", ct[:, 0], ct[:, 1])
cm = np.array(P.COAMING_TOP_Z); report("COAMING_TOP_Z", cm[:, 0], cm[:, 1])
