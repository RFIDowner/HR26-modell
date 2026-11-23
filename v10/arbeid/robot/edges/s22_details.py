import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from corner import densify
from secplot import plot_sections
T = np.load(OUT + "/ours_full.npy"); B = np.load(OUT + "/bambu_full_nostretch.npy")
W = OUT + "/work"
# 1) window recess at x=4300: ours vs bambu
for nm, M_, box in (("ours", T, (900, 1200, 850, 1200)), ("bam", B, (850, 1050, 950, 1350))):
    s = section(M_, 0, 4300.0)[:, :, [1, 2]]
    np.save(f"{W}/seg_{nm}_x4300.npy", s)
    plot_sections([(s, (200, 0, 0) if nm == "ours" else (0, 60, 220), 2)], box, W=600, grid=10, title=f"{nm} x=4300 window", fn=f"{W}/z_{nm}_x4300.png")
P = densify(np.load(f"{W}/seg_ours_x4300.npy"))
Q = P[(P[:, 0] > 1000) & (P[:, 1] > 850) & (P[:, 1] < 1150)]
for z in range(880, 1150, 15):
    r = Q[np.abs(Q[:, 1] - z) < 1.5]
    if len(r): print(" ours x4300 z", z, "outer y", np.round(r[:, 0].max(), 1))
P = densify(np.load(f"{W}/seg_bam_x4300.npy"))
Q = P[(P[:, 0] > 900) & (P[:, 1] > 950) & (P[:, 1] < 1350)]
for z in range(960, 1340, 15):
    r = Q[np.abs(Q[:, 1] - z) < 1.5]
    if len(r): print(" bam x4300 z", z, "outer y", np.round(r[:, 0].max(), 1))
