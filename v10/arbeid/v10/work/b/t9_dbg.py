import sys, time
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
import numpy as np, cadquery as cq
from hr26 import hull as H, params as P
pts, nrm = H._strake_path()
d = np.diff(pts[:, :2], axis=0); a = np.degrees(np.arctan2(d[:, 1], d[:, 0])); k = (np.diff(a) + 180) % 360 - 180
L = np.hypot(d[:, 0], d[:, 1])
for i in range(len(k)):
    if pts[i+1, 0] > 7700 and pts[i+1,1] > 500:
        print("%4d (%7.1f,%6.1f) seg %5.1f turn %6.2f nz %.3f" % (i+1, pts[i+1,0], pts[i+1,1], L[i], k[i], nrm[i+1,2]))
