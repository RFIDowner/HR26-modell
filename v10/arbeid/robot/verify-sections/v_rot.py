"""Find the bed rotation of 01_skrog.stl independently (mirror symmetry)."""
import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-sections")
from v_stl_lib import load_stl, rot_z

T = load_stl(r"C:/Users/stig/Documents/GitHub/HR26-modell/export/stl/01_skrog.stl")
print("triangles", len(T), "bbox", T.reshape(-1, 3).min(0).round(2), T.reshape(-1, 3).max(0).round(2))
V0 = T.reshape(-1, 3)
res = []
for a in np.arange(43.0, 46.51, 0.05):
    V = rot_z(V0, -a)
    x = V[:, 0]; L = x.max() - x.min()
    xb = np.floor((x - x.min()) / L * 60).astype(int)
    mids = []
    for k in range(6, 54):
        m = xb == k
        if m.sum() < 20:
            continue
        mids.append(0.5 * (V[m, 1].max() + V[m, 1].min()))
    mids = np.array(mids)
    res.append((a, mids.std(), np.ptp(V[:, 1]), L))
res = np.array(res)
i = np.argmin(res[:, 1])
print("best angle by midline straightness: %.2f deg (std %.4f mm)" % (res[i, 0], res[i, 1]))
for a in (44.0, 45.0):
    j = np.argmin(np.abs(res[:, 0] - a))
    print("  angle %.2f: midline std %.4f mm, y-extent %.3f, x-extent %.3f" % tuple(res[j]))
# keel-only check: points with z < 5 mm (keel tip region)
for a in (44.0, 45.0, res[i, 0]):
    V = rot_z(V0, -a)
    k = V[V[:, 2] < 3.0]
    A = np.c_[k[:, 0], np.ones(len(k))]
    sl = np.linalg.lstsq(A, k[:, 1], rcond=None)[0][0]
    print("  angle %.2f: keel-bottom y-vs-x slope %.5f -> residual yaw %.3f deg (n=%d, x-span %.1f mm)" % (a, sl, np.degrees(np.arctan(sl)), len(k), np.ptp(k[:, 0])))
