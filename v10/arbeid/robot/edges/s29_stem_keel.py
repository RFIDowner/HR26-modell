import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from corner import corner, fmt, min_radius, densify
T = np.load(OUT + "/ours_full.npy"); B = np.load(OUT + "/bambu_full_nostretch.npy")
for nm, M_, z in (("OURS", T, 1000.0), ("OURS", T, 1100.0), ("BAMBU", B, 1100.0), ("BAMBU", B, 1200.0)):
    s = section(M_, 2, z)[:, :, [0, 1]]
    P = densify(s)
    Q = P[np.abs(P[:, 1]) < 60]
    xb = Q[:, 0].min()
    # half-angle of entrance from points 80-200 mm aft of the tip
    sel = P[(P[:, 0] > xb + 80) & (P[:, 0] < xb + 200) & (P[:, 1] > 0)]
    sel2 = P[(P[:, 0] > xb + 80) & (P[:, 0] < xb + 200) & (P[:, 1] < 0)]
    r = corner(s, (xb + 80, xb + 200, 0.5, sel[:, 1].max() + 1), (xb + 80, xb + 200, sel2[:, 1].min() - 1, -0.5), search=600)
    mr = min_radius(s, (xb, 0.0), arc=80, w=5.0, step=0.5)
    print(f"{nm} stem plan z={z:.0f}: tip x {xb:.0f}; {fmt('', r)}")
    print(f"      3-pt Rmin(w=5) {mr[0]:.1f} mm full at ({mr[1]:.0f},{mr[2]:.0f})")
# keel root: transverse section x=4500, concave corner hull bottom/keel side
s = section(T, 0, 4500.0)[:, :, [1, 2]]
P = densify(s)
Q = P[(P[:, 1] < -150) & (P[:, 1] > -450) & (P[:, 0] > 0) & (P[:, 0] < 400)]
for z in range(-400, -150, 20):
    r = Q[np.abs(Q[:, 1] - z) < 1.5]
    if len(r): print(" x4500 keel/hull z", z, "outer y", np.round(np.sort(r[:, 0])[-3:], 1))
