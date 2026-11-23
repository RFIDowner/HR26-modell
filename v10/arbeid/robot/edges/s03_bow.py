import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *

T = np.load(OUT + "/ours_full.npy")
V = T.reshape(-1, 3)
# vertices of the anchor-roller block region
sel = V[(V[:, 0] < 800) & (V[:, 2] > 1215) & (np.abs(V[:, 1]) < 200)]
print("verts above deck near bow: x range", sel[:, 0].min().round(1), sel[:, 0].max().round(1),
      "y range", sel[:, 1].min().round(1), sel[:, 1].max().round(1), "z range", sel[:, 2].min().round(1), sel[:, 2].max().round(1))
# section at y=0, chained, region x<900
seg = section(T, 1, 0.0)[:, :, [0, 2]]
lines = chain(seg, tol=1e-3)
for L in lines:
    m = (L[:, 0] < 900) & (L[:, 1] > 600)
    if m.sum() > 3:
        print("polyline with", len(L), "pts; bow part:")
        Q = L[m]
        for p in Q[:: max(1, len(Q) // 60)]:
            print(f"   x {p[0]:7.1f}  z {p[1]:7.1f}")
# analytic stem
P_LWL_FWD = 1008.0
for z in (800, 900, 1000, 1100, 1150, 1200):
    t = (z / 1204.0) ** (1 / 1.3)
    print("analytic stem z", z, "x", round(P_LWL_FWD * (1 - t), 1))
