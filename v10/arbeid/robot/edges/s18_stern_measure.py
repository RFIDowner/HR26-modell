import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from corner import corner, fmt, densify
W = OUT + "/work"
S = lambda nm: np.load(f"{W}/seg_{nm}.npy")
op = S("ours_plan_z600"); bp = S("bam_plan_z600"); osc = S("ours_stern_cl"); bsc = S("bam_stern_cl")
print(fmt("OURS transom/side plan z600", corner(op, (7836, 7870, 440, 600), (7700, 7800, 650, 760), search=60)))
print(fmt("BAMBU transom/side plan z600", corner(bp, (7712, 7735, 340, 440), (7480, 7600, 520, 580), search=80)))
print(fmt("OURS transom top (y=0)", corner(osc, (7925, 7945, 870, 950), (7760, 7930, 965, 1000))))
print(fmt("BAMBU transom top (y=0)", corner(bsc, (7816, 7842, 900, 1080), (7650, 7760, 1130, 1145))))
# turning analysis along ours plan polyline near the corner: list vertices & kink angles
P = op
lines = chain(op[:, :, :], tol=1e-3)
for L in lines:
    m = (L[:, 0] > 7650) & (L[:, 1] > 400) & (L[:, 1] < 800)
    if m.sum() > 5:
        Q = L[m]
        d = np.diff(Q, axis=0); a = np.degrees(np.arctan2(d[:, 1], d[:, 0])); l = np.hypot(d[:, 0], d[:, 1])
        k = np.diff(a); k = (k + 180) % 360 - 180
        print("ours z600 polyline vertices (x,y), facet length, kink deg:")
        for i in range(len(Q) - 2):
            if l[i] > 0.5 or abs(k[i]) > 1:
                print(f"   ({Q[i+1,0]:7.1f},{Q[i+1,1]:6.1f})  facet {l[i]:6.1f}  kink {k[i]:6.1f}")
        break
