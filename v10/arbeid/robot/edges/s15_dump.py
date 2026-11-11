import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from corner import densify
W = OUT + "/work"
def dump(nm, ubox, vbox, by="v", step=10):
    P = densify(np.load(f"{W}/seg_{nm}.npy"))
    Q = P[(P[:, 0] >= ubox[0]) & (P[:, 0] <= ubox[1]) & (P[:, 1] >= vbox[0]) & (P[:, 1] <= vbox[1])]
    print("---", nm)
    if by == "v":
        for v in np.arange(vbox[0], vbox[1], step):
            r = Q[np.abs(Q[:, 1] - v) < 2.0]
            if len(r): print(f" v {v:6.0f}: u", np.unique(np.round(r[:, 0] / 2) * 2)[:14])
    else:
        for u in np.arange(ubox[0], ubox[1], step):
            r = Q[np.abs(Q[:, 0] - u) < 2.0]
            if len(r): print(f" u {u:6.0f}: v", np.unique(np.round(r[:, 1] / 2) * 2)[:14])
dump("bam_x6300", (300, 520), (1150, 1380), "v", 10)
dump("bam_cl_front", (1300, 1700), (1200, 1420), "u", 10)
