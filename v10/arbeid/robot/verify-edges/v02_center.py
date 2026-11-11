import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-edges")
from vlib import *
F = ours_full(-45.0)
np.save("ours_full.npy", F)
V = F.reshape(-1,3)
print("x range", V[:,0].min(), V[:,0].max(), " z range", V[:,2].min(), V[:,2].max(), " y", V[:,1].min(), V[:,1].max())
# centreline section, y = 0.5 to avoid on-plane vertices
L = section_lines(F, 1, 0.5, keep=(0,2))
P = np.vstack(L)
def window(x0,x1,z0,z1):
    m = (P[:,0]>=x0)&(P[:,0]<=x1)&(P[:,1]>=z0)&(P[:,1]<=z1)
    return P[m]
print("\n--- coachroof front, centreline: points x 2150..2400, z 1150..1420 (sorted by z)")
W = window(2150,2400,1150,1420)
W = W[np.argsort(W[:,1])]
for p in W[::max(1,len(W)//40)]:
    print(f"  x={p[0]:8.1f} z={p[1]:7.1f}")
print("\n--- bow, centreline: x 0..800, z 700..1450")
W = window(0,800,700,1450)
# report: for z levels, min x of material boundary
for z in (793, 800, 850, 900, 947, 1000, 1100, 1150, 1200, 1250, 1300, 1350):
    m = np.abs(W[:,1]-z) < 6
    xs = np.sort(W[m,0])
    print(f"  z~{z}: boundary x values {np.round(xs[:8],1)}")
