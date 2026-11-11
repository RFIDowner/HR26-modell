"""Independent check of the longitudinal curve claims (curves-2,3,4,5,6,8)."""
import sys, csv
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-curves/repo")
import numpy as np
from hr26 import curves as C, params as P

np.set_printoptions(precision=2, suppress=True, linewidth=150)
REPO = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-curves/repo/"


def kinks(xs, ys, label, only_abs=0.0):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    s = np.diff(ys) / np.diff(xs)
    a = np.degrees(np.arctan(s))
    d = np.diff(a)
    out = [(xs[i + 1], d[i]) for i in range(len(d)) if abs(d[i]) >= only_abs]
    print(f"{label}: kinks (x, dAngle deg):", ", ".join(f"{x:.0f}:{v:+.2f}" for x, v in out))
    # sign changes of the turning (= curvature sign changes for a polyline)
    sg = np.sign(d[np.abs(d) > 1e-6])
    print(f"   turning sign changes: {int((np.diff(sg) != 0).sum())}")
    return d

# ---------------- raw trace
raw = np.loadtxt(REPO + "data/deck_halfbreadth.csv", delimiter=",", skiprows=1)
tab = np.loadtxt(REPO + "data/hull_stations.csv", delimiter=",", skiprows=1)
X = tab[:, 0]
print("CSV deck column vs raw trace interpolated at the 150 grid:")
dv = tab[:, 1] - np.interp(X, raw[:, 0], raw[:, 1])
print("   max |diff| =", np.abs(dv).max(), "at x =", X[np.argmax(np.abs(dv))], " (x>=7300 rows:", dv[X >= 7300], ")")
print("raw trace x range", raw[0, 0], raw[-1, 0], "n=", len(raw), "max", raw[:, 1].max(), "at", raw[np.argmax(raw[:, 1]), 0])

# ---------------- deck_half_breadth as used
print("\n== deck_half_breadth")
for x in [7299.999, 7300.0, 7350.0]:
    print(f"  hb({x}) = {C.deck_half_breadth(x):.2f}")
print("  _HB at 7300 (faired table):", np.interp(7300, C._X, C._HB), " STERN_OUTLINE at 7350:", np.interp(7350, C._SX, C._SY), " faired _HB at 7350:", np.interp(7350, C._X, C._HB))
print("  hb(300) used:", C.deck_half_breadth(300.0), " CSV:", np.interp(300, X, tab[:, 1]), " raw:", np.interp(300, raw[:, 0], raw[:, 1]))
print("  hb(150) used:", C.deck_half_breadth(150.0), " CSV:", np.interp(150, X, tab[:, 1]), " raw:", np.interp(150, raw[:, 0], raw[:, 1]))
print("  hb(450) used:", C.deck_half_breadth(450.0), " CSV:", np.interp(450, X, tab[:, 1]), " raw:", np.interp(450, raw[:, 0], raw[:, 1]))
xx = np.arange(0, 7950.1, 1.0)
hb = np.array([C.deck_half_breadth(x) for x in xx])
print("  max used hb:", hb.max(), "at", xx[hb.argmax()], " raw max:", raw[:, 1].max(), " -> beam used", 2 * hb.max())
# kinks of the used deck function at its nodes
nodes = sorted(set([x for x in C._X if x < C._SX[0]] + list(C._SX)))
nodes = [x for x in nodes if x <= 7891]
yn = [C.deck_half_breadth(x) for x in nodes]
kinks(nodes, yn, "deck hb (used, nodes)", only_abs=0.0)
# discrepancy between used function and raw trace (x<7300) and STERN_OUTLINE
m = raw[:, 0] < 7300
d_used = np.array([C.deck_half_breadth(x) for x in raw[m, 0]]) - raw[m, 1]
print("  used - raw trace (x<7300): max |d| = %.1f at x=%.0f, max+ %.1f, max- %.1f" % (np.abs(d_used).max(), raw[m, 0][np.argmax(np.abs(d_used))], d_used.max(), d_used.min()))
for lo, hi in [(0, 2450), (2450, 3250), (3250, 7300)]:
    mm = (raw[m, 0] >= lo) & (raw[m, 0] < hi)
    print(f"     range {lo}-{hi}: max|d| {np.abs(d_used[mm]).max():.1f}")

# ---------------- sheer
print("\n== sheer_z")
de = np.array(P.DECK_EDGE_Z)
for x in [1000, 2000, 2500, 3000, 4200, 6500, 7000, 7200, 7400, 7600, 7800]:
    print(f"  x={x}: sheer_z={C.sheer_z(x):.1f} table={np.interp(x, de[:,0], de[:,1]):.1f} diff={C.sheer_z(x)-np.interp(x, de[:,0], de[:,1]):+.1f}")
zsu = np.array([C.sheer_z(x) for x in de[:, 0]])
print("  max |sheer_z - DECK_EDGE_Z| at table points:", np.abs(zsu - de[:, 1]).max(), "at", de[np.argmax(np.abs(zsu - de[:, 1])), 0])
print("  slopes 2500-5000:", np.diff(de[3:10, 1]) / np.diff(de[3:10, 0]))
kinks(de[:, 0], de[:, 1], "DECK_EDGE_Z table")
# 4200 above chord 3750-4500
print("  4200 point above 3750-4500 chord by", 1115 - np.interp(4200, [3750, 4500], [1122, 1105]))
kinks(C._X, C._ZS, "sheer_z (faired, at 150 grid)")

# ---------------- strake
print("\n== strake_z")
kinks(C._X, C._ZK, "strake_z faired")
kinks(X, tab[:, 2], "strake CSV raw")

# ---------------- bottom
print("\n== bottom_z")
for x in [999.6, 1000, 1007, 1007.9, 1008, 1010, 1050, 1221]:
    print(f"  bottom_z({x}) = {C.bottom_z(x):.1f}")
print("  CSV canoe bottom at 1008 (interp raw CSV):", np.interp(1008, X, tab[:, 3]), "  faired _ZB at 1008:", np.interp(1008, C._X, C._ZB))
kinks(C._X[C._X >= 1050], C._ZB[C._X >= 1050], "bottom_z faired (x>=1050)", only_abs=2.0)

# ---------------- waterplane, fullness
print("\n== wl_half_breadth / fullness")
wp = np.array(P.WATERPLANE)
xw = P.LWL_FWD + wp[:, 0] * P.LWL
yw = C._BW_MAX * wp[:, 1]
print("  _BW_MAX =", C._BW_MAX)
kinks(xw, yw, "wl_half_breadth nodes (full-scale angles)")
sf = np.array(P.SECTION_FULLNESS)
xs_ = sf[:, 0] * P.LOA
dm = np.diff(sf[:, 1]) / np.diff(xs_) * 1000.0
print("  fullness nodes x:", xs_)
print("  dm/dx per m on intervals:", dm, "\n  jumps at nodes:", np.diff(dm))

st = C.stations(40)
xs = [x for x in st if 6.0 < x < P.LOA - 4.0]
xs = sorted(set([4.0] + xs + [7850.0, 7910.0] + [P.LOA - 2.0]))
xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 8.0]
print("\nloft stations (n=%d):" % len(xs), np.array(xs))
np.save(r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-curves/stations.npy", np.array(xs))

# ---------------- deckhouse tables
print("\n== deckhouse")
kinks([p[0] for p in P.COACH_TOP], [p[1] for p in P.COACH_TOP], "COACH_TOP")
ct = np.array(P.COAMING_TOP_Z)
kinks(ct[:, 0], ct[:, 1], "COAMING_TOP_Z")
for i in range(1, len(ct) - 1):
    ch = np.interp(ct[i, 0], [ct[i-1, 0], ct[i+1, 0]], [ct[i-1, 1], ct[i+1, 1]])
    print(f"   {ct[i,0]:.0f}: point - chord of neighbours = {ct[i,1]-ch:+.1f}")
