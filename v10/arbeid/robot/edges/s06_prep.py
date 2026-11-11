import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
T = ours_full(); np.save(OUT + "/ours_full.npy", T)
B = bambu_full(stretch_y=True); B[:, :, 0] += 4266.35; np.save(OUT + "/bambu_full.npy", B)
B0 = bambu_full(stretch_y=False); B0[:, :, 0] += 4266.35; np.save(OUT + "/bambu_full_nostretch.npy", B0)
# manifold check of Bambu: count edge uses
V = B0.reshape(-1, 3)
uv, inv = np.unique(np.round(V, 4), axis=0, return_inverse=True)
F = inv.reshape(-1, 3)
E = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
ue, cnt = np.unique(E, axis=0, return_counts=True)
print("bambu unique verts", len(uv), "edges", len(ue), "edge use counts:", {int(k): int((cnt == k).sum()) for k in np.unique(cnt)})
# typical triangle edge length in full-scale mm, for hull region
L = np.linalg.norm(B0[:, 1] - B0[:, 0], axis=1)
print("bambu edge length full-scale mm: median", np.median(L).round(1), "p90", np.percentile(L, 90).round(1))
L2 = np.linalg.norm(T[:, 1] - T[:, 0], axis=1)
print("ours edge length full-scale mm: median", np.median(L2).round(1), "p90", np.percentile(L2, 90).round(1))
