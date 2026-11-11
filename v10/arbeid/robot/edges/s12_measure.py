import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from corner import corner, fmt
W = OUT + "/work"
S = lambda nm: np.load(f"{W}/seg_{nm}.npy")
o3 = S("ours_x3200")
# dump key points on ours x3200 outer contour for sanity
P = o3.reshape(-1, 2)
sel = P[(P[:, 0] > 1050) & (P[:, 1] > 1000) & (P[:, 1] < 1200)]
print("ours x3200 max y in z 1000-1200:", sel[:, 0].max().round(1), "at z", sel[np.argmax(sel[:, 0]), 1].round(1))
print(fmt("ours deck edge x3200", corner(o3, (1060, 1140, 1050, 1125), (960, 1110, 1120, 1160))))
print(fmt("ours coachroof roof edge x3200", corner(o3, (905, 940, 1180, 1330), (700, 900, 1330, 1380))))
print(fmt("ours coachroof base x3200", corner(o3, (905, 940, 1180, 1330), (960, 1110, 1120, 1160))))
o6 = S("ours_x6300")
print(fmt("ours coaming inner top x6300", corner(o6, (835, 860, 960, 1110), (860, 970, 1110, 1145))))
print(fmt("ours coaming outer top x6300", corner(o6, (972, 990, 1092, 1122), (860, 970, 1110, 1145))))
of = S("ours_cl_front")
print(fmt("ours coachroof front top (cl)", corner(of, (2185, 2215, 1235, 1335), (2215, 2450, 1340, 1370))))
print(fmt("ours coachroof front base (cl)", corner(of, (2185, 2215, 1235, 1335), (2050, 2185, 1195, 1235))))
