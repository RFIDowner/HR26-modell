import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from corner import densify, corner, fmt
W = OUT + "/work"
def dump(nm, ubox, vbox, by="v", step=10):
    P = densify(np.load(f"{W}/seg_{nm}.npy"))
    Q = P[(P[:, 0] >= ubox[0]) & (P[:, 0] <= ubox[1]) & (P[:, 1] >= vbox[0]) & (P[:, 1] <= vbox[1])]
    print("---", nm)
    rng = np.arange(vbox[0], vbox[1], step) if by == "v" else np.arange(ubox[0], ubox[1], step)
    for t in rng:
        r = Q[np.abs(Q[:, 1 if by == "v" else 0] - t) < 2.0]
        if len(r): print(f" {by} {t:6.0f}:", np.unique(np.round(r[:, 0 if by == "v" else 1] / 2) * 2)[:10])
dump("bam_plan_z600", (7500, 7800), (350, 700), "v", 20)
dump("bam_stern_cl", (7700, 7900), (900, 1200), "v", 10)
dump("ours_plan_z600", (7700, 7900), (450, 750), "v", 20)
