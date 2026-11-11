import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *

def xs_at(seg2, zf):
    """seg2: (M,2,2) segments in (u, z); return u values where segments cross z=zf."""
    a, b = seg2[:, 0], seg2[:, 1]
    da, db = a[:, 1] - zf, b[:, 1] - zf
    cr = da * db < 0
    t = da[cr] / (da[cr] - db[cr])
    return a[cr, 0] + t * (b[cr, 0] - a[cr, 0])

T = np.load(OUT + "/ours_full.npy")
B = np.load(OUT + "/bambu_full_nostretch.npy")
so = section(T, 1, 0.0)[:, :, [0, 2]]
sb = section(B, 1, 0.0)[:, :, [0, 2]]
print(" z    ours: min x / max x       bambu: min x / max x")
for zf in (200, 300, 400, 500, 600, 700, 800, 900, 1000, 1093, 1150, 1200, 1250, 1300, 1350):
    xo = xs_at(so, zf); xb = xs_at(sb, zf)
    print(f"{zf:5d}  {xo.min() if len(xo) else np.nan:8.0f} {xo.max() if len(xo) else np.nan:8.0f}     {xb.min() if len(xb) else np.nan:8.0f} {xb.max() if len(xb) else np.nan:8.0f}   n={len(xb)}")
# Bambu x at the bow at z=1093 vs ours
xo = xs_at(so, 1093).min(); xb = xs_at(sb, 1093).min()
print("shift for bambu x:", xo - xb)
# plan view half-breadth at z=1093 (our max-beam height) along x
for zf in (1093,):
    for T_, nm in ((T, "ours"), (B, "bambu")):
        s = section(T_, 2, zf)[:, :, [0, 1]]
        P = s.reshape(-1, 2)
        P = P[P[:, 1] > 0]
        print(nm, "x range at z", zf, P[:, 0].min().round(0), P[:, 0].max().round(0), "max y", P[:, 1].max().round(0))
