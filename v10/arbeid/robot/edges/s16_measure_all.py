import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from corner import corner, fmt, bump, densify, in_box
W = OUT + "/work"
S = lambda nm: np.load(f"{W}/seg_{nm}.npy")
print("=== OURS ===")
o3 = S("ours_x3200"); o6 = S("ours_x6300"); of = S("ours_cl_front"); osc = S("ours_stern_cl"); op = S("ours_plan_z600")
print(fmt("deck edge x3200", corner(o3, (1060, 1140, 1050, 1125), (960, 1110, 1120, 1160))))
print(fmt("coachroof roof edge x3200", corner(o3, (905, 940, 1180, 1330), (700, 900, 1330, 1380))))
print(fmt("coaming inner top x6300", corner(o6, (835, 860, 960, 1110), (860, 970, 1110, 1145))))
print(fmt("coaming outer top x6300", corner(o6, (972, 990, 1092, 1122), (860, 970, 1110, 1145))))
print(fmt("coachroof front top (y=0)", corner(of, (2185, 2215, 1235, 1335), (2215, 2450, 1340, 1370))))
print(fmt("transom top edge (y=0)", corner(osc, (7925, 7945, 870, 950), (7760, 7930, 965, 1000))))
print(fmt("transom/side corner plan z600", corner(op, (7835, 7880, 520, 620), (7700, 7815, 650, 760))))
# strake rectangle at x3200: outer corners
P = densify(o3)
st = P[(P[:, 1] > 820) & (P[:, 1] < 960) & (P[:, 0] > 1050)]
print("strake region y max", st[:, 0].max().round(1), "z of strake faces:", np.unique(np.round(st[st[:, 0] > st[:, 0].max() - 2, 1])).min(), np.unique(np.round(st[st[:, 0] > st[:, 0].max() - 2, 1])).max())
print("=== BAMBU (k=0.3708, no y stretch) ===")
b3 = S("bam_x3200"); b6 = S("bam_x6300"); bf = S("bam_cl_front"); bsc = S("bam_stern_cl"); bp = S("bam_plan_z600")
print(fmt("deck edge x3200 (topside->deck)", corner(b3, (944, 976, 1090, 1280), (720, 860, 1285, 1310))))
r = bump(b3, (895, 940, 1310, 1340)); print("toe rail crown x3200: R %.1f (rms %.1f) width %.0f height %.0f n=%d" % (r[0][2], r[0][3], r[1], r[2], r[3]))
r = bump(b3, (976, 995, 1015, 1066)); print("strake crown x3200:   R %.1f (rms %.1f) width %.0f height %.0f n=%d" % (r[0][2], r[0][3], r[1], r[2], r[3]))
print(fmt("coachroof roof edge x3200", corner(b3, (640, 680, 1310, 1450), (350, 600, 1468, 1500))))
print(fmt("coaming inner top x6300", corner(b6, (320, 336, 1160, 1320), (355, 395, 1345, 1362))))
print(fmt("coachroof front top (y=0)", corner(bf, (1398, 1418, 1262, 1340), (1440, 1555, 1374, 1392))))
print(fmt("coachroof front base (y=0)", corner(bf, (1398, 1418, 1262, 1340), (1250, 1385, 1228, 1244))))
