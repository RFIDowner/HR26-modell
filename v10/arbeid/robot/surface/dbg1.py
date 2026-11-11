import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface")
from common import *
sys.path.insert(0, REPO)
from hr26 import curves as C, params as P
D = np.load(OUT + "/a1.npz")
Vf, F, fn, cls, d, area = D["Vf"], D["F"], D["fn"], D["cls"], D["d"], D["area"]
c = Vf[F].mean(1)
# outward-facing side faces on starboard, z between 100 and 700 (topsides below strake)
m = (cls != 6) & (np.abs(fn[:, 1]) > 0.6) & (c[:, 2] > 100) & (c[:, 2] < 700) & (c[:, 1] * fn[:, 1] > 0)
print("candidate faces", m.sum(), "area", area[m].sum())
for x0 in range(500, 8000, 500):
    mm = m & (c[:, 0] > x0 - 250) & (c[:, 0] < x0 + 250)
    if mm.sum():
        print(x0, mm.sum(), "d percentiles", np.round(np.percentile(d[mm], [5, 25, 50, 75, 95]), 1))
# cls 0 area by z band and normal
m0 = cls == 0
print("class0 area by normal type: up", area[m0 & (fn[:,2] > 0.7)].sum(), " side", area[m0 & (np.abs(fn[:,1]) > 0.6)].sum(), " down", area[m0 & (fn[:,2] < -0.7)].sum())
mm = m0 & (np.abs(fn[:,1]) > 0.6)
print("class0 side faces z full percentiles", np.percentile(c[mm,2], [5,25,50,75,95]))
print("class0 side d percentiles", np.percentile(d[mm][~np.isnan(d[mm])], [5,25,50,75,95]))
