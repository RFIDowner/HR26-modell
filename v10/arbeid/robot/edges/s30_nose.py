import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
sys.path.insert(1, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges/repo")
import numpy as np
from lib import *
T = np.load(OUT + "/ours_full.npy")
cap = T[(np.abs(T[:, :, 0] - 4.0) < 0.6).all(1)]
V = cap.reshape(-1, 3)
area = 0.5 * np.linalg.norm(np.cross(cap[:, 1] - cap[:, 0], cap[:, 2] - cap[:, 0]), axis=1).sum()
print("triangles in plane x=4:", len(cap), " y", V[:, 1].min().round(1), V[:, 1].max().round(1), " z", V[:, 2].min().round(1), V[:, 2].max().round(1), " area mm2", round(area))
from hr26 import curves as C
for x in (0, 4, 20, 50, 100, 200):
    print(f" code: x={x:4d} deck half-breadth {C.deck_half_breadth(x):6.1f}  sheer {C.sheer_z(x):6.1f}  stem/bottom z {C.bottom_z(x):6.1f}")
# measured raw deck outline from data
import csv
rows = list(csv.reader(open("C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges/repo/data/deck_halfbreadth.csv")))
print(rows[0], rows[1:6])
