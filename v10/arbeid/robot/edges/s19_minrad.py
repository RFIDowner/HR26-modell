import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from corner import min_radius
W = OUT + "/work"
S = lambda nm: np.load(f"{W}/seg_{nm}.npy")
jobs = [
 ("OURS  deck edge x3200", "ours_x3200", (1132, 1143)),
 ("BAMBU deck edge/toe rail x3200", "bam_x3200", (930, 1312)),
 ("OURS  coachroof roof edge x3200", "ours_x3200", (922, 1354)),
 ("BAMBU coachroof roof edge x3200", "bam_x3200", (639, 1473)),
 ("OURS  coaming inner top x6300", "ours_x6300", (850, 1126)),
 ("BAMBU coaming inner top x6300", "bam_x6300", (335, 1351)),
 ("OURS  coachroof front top y0", "ours_cl_front", (2200, 1350)),
 ("BAMBU coachroof front top y0", "bam_cl_front", (1418, 1374)),
 ("OURS  transom top y0", "ours_stern_cl", (7946, 958)),
 ("BAMBU transom top y0", "bam_stern_cl", (7845, 1130)),
 ("OURS  transom/side plan z600", "ours_plan_z600", (7825, 631)),
 ("BAMBU transom/side plan z600", "bam_plan_z600", (7702, 482)),
]
for w in (5.0, 10.0):
    print(f"--- 3-point radius with points +-{w} mm apart (min over +-60 mm of contour)")
    for nm, sg, C in jobs:
        r = min_radius(S(sg), C, arc=60.0, w=w, step=0.5)
        print(f"  {nm:34s}  Rmin {r[0]:7.1f} mm full ({r[0]/30:5.2f} mm model) at ({r[1]:.0f},{r[2]:.0f})" if r else f"  {nm}: none")
