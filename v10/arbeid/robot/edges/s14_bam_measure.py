import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from corner import corner, fmt, bump, densify, in_box
W = OUT + "/work"
S = lambda nm: np.load(f"{W}/seg_{nm}.npy")
b3 = S("bam_x3200")
P = densify(b3)
# print outer contour samples right side (y>600), z 1000-1500, sorted by z
Q = P[(P[:, 0] > 600) & (P[:, 1] > 1000) & (P[:, 1] < 1520)]
for zz in range(1000, 1500, 10):
    r = Q[np.abs(Q[:, 1] - zz) < 2.5]
    if len(r):
        print(f"z {zz}: y values", np.unique(np.round(r[:, 0] / 2) * 2)[:12])
