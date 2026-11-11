import sys, time
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface")
from common import *
from PIL import Image
D = np.load(OUT + "/a1.npz")
V, F, fn, cls = D["V"], D["F"], D["fn"], D["cls"]
keep = cls != 6
F2 = F[keep]; fn2 = fn[keep]
t = time.time()
cn = corner_normals(V, F2, fn2)
print("corner normals %.1fs" % (time.time() - t))
R = look(140, 18)
t = time.time()
rr = raster(V, F2, R, 900)
print("raster %.1fs" % (time.time() - t), rr["H"])
for mode in ("flat", "smooth", "zebra"):
    Image.fromarray(shade2(rr, fn2, cn, R, mode)).save(OUT + f"/test_{mode}.png")
