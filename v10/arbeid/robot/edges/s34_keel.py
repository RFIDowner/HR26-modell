import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from corner import densify, min_radius
T = np.load(OUT + "/ours_full.npy")
s = section(T, 0, 4500.0)[:, :, [1, 2]]
P = densify(s)
Q = P[(P[:, 1] < -100) & (P[:, 1] > -600) & (P[:, 0] > 0) & (P[:, 0] < 600)]
for z in range(-560, -100, 20):
    r = Q[np.abs(Q[:, 1] - z) < 1.0]
    if len(r): print(" x4500 z", z, "outer y", np.round(np.sort(r[:, 0])[-1], 1))
