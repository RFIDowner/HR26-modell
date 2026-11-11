import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface")
from common import *
T32 = load_raw(OURS)
V0, F = weld(T32)
lab = components(len(V0), F)
ul, cnt = np.unique(lab, return_counts=True)
Fo = F[lab == ul[np.argmax(cnt)]]
def cut_pts(V, Fo, x0):
    A = V[Fo]; X = A[:, :, 0]
    sel = (X.min(1) < x0) & (X.max(1) > x0); P = A[sel]
    pts = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        pa, pb = P[:, a], P[:, b]
        cr = (pa[:, 0] - x0) * (pb[:, 0] - x0) < 0
        t = (x0 - pa[cr, 0]) / (pb[cr, 0] - pa[cr, 0])
        pts.append(pa[cr] + t[:, None] * (pb[cr] - pa[cr]))
    return np.concatenate(pts)
def mids_for(a):
    V = rotz(V0, -a)
    xs = np.linspace(V[:, 0].min() + 30, V[:, 0].max() - 30, 15)
    out = []
    for x in xs:
        p = cut_pts(V, Fo, x)
        p = p[(p[:, 2] > 50) & (p[:, 2] < 75)]
        out.append(0.5 * (p[:, 1].max() + p[:, 1].min()))
    return xs, np.array(out)
best = None
for a in np.arange(44.0, 46.001, 0.05):
    xs, mids = mids_for(a)
    r = np.std(mids)
    if best is None or r < best[1]:
        best = (round(a, 3), r)
print("best angle", best)
for a in (44.0, 45.0):
    xs, mids = mids_for(a)
    print(f"at {a}: centre offsets (model mm):", np.round(mids - mids.mean(), 3))
