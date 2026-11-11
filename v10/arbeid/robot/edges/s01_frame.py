import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *

T = ours_full()
V = T.reshape(-1, 3)
print("ours tris", len(T))
print("ours bbox min", V.min(0).round(1), "max", V.max(0).round(1))
np.save(OUT + "/ours_full.npy", T)
# centreline profile section y=0
seg = section(T, 1, 0.0)
P = seg.reshape(-1, 3)
for zf in (100, 300, 600, 900, 1000, 1100, 1200):
    sel = P[np.abs(P[:, 2] - zf) < 6]
    if len(sel):
        print(f"  ours y=0, z={zf}: min x {sel[:,0].min():.0f}  max x {sel[:,0].max():.0f}")
print("max |y|", np.abs(V[:, 1]).max().round(1))

B = bambu_full(stretch_y=False)
Vb = B.reshape(-1, 3)
print("bambu tris", len(B))
print("bambu bbox min", Vb.min(0).round(1), "max", Vb.max(0).round(1))
np.save(OUT + "/bambu_full_nostretch.npy", B)
segb = section(B, 1, 0.0)
Pb = segb.reshape(-1, 3)
for zf in (300, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300):
    sel = Pb[np.abs(Pb[:, 2] - zf) < 6]
    if len(sel):
        print(f"  bambu y=0, z={zf}: min x {sel[:,0].min():.0f}  max x {sel[:,0].max():.0f}")
# max beam height for bambu: z at max |y| in mid third
mid = Vb[(Vb[:, 0] > Vb[:, 0].min() + 0.3 * 7950) & (Vb[:, 0] < Vb[:, 0].min() + 0.7 * 7950) & (Vb[:, 2] < 1500)]
i = np.argmax(np.abs(mid[:, 1]))
print("bambu max |y| (no stretch)", abs(mid[i, 1]).round(0), "at x", mid[i, 0].round(0), "z", mid[i, 2].round(0))
print("bambu min z of hull", Vb[Vb[:, 2] < 1500][:, 2].min().round(0))
