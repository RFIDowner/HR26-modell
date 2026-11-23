"""Exact plane sections of the baseline mesh (full-scale boat frame)."""
import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/py")
from stl import load_full
V, F = load_full()
T = V[F]                       # (n,3,3)
TX = T[:, :, 0]; TXmin = TX.min(1); TXmax = TX.max(1)
TZ = T[:, :, 2]; TZmin = TZ.min(1); TZmax = TZ.max(1)


def slice_axis(c, axis=0):
    """Return segments (m,2,3) of intersection of mesh with plane coord[axis]=c."""
    if axis == 0:
        m = (TXmin <= c) & (TXmax >= c)
    else:
        A = T[:, :, axis]; m = (A.min(1) <= c) & (A.max(1) >= c)
    t = T[m]
    d = t[:, :, axis] - c
    segs = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        di, dj = d[:, i], d[:, j]
        cross = (di * dj) < 0
        s = np.where(cross, di / (di - dj + 1e-30), np.nan)
        P = t[:, i] + (t[:, j] - t[:, i]) * s[:, None]
        segs.append(P)
    P = np.stack(segs, 1)          # (k,3 edges,3)
    ok = ~np.isnan(P[:, :, 0])
    out = []
    for k in range(len(P)):
        q = P[k][ok[k]]
        if len(q) >= 2:
            out.append(q[:2])
    return np.array(out)


def section_points(x):
    s = slice_axis(x, 0)
    return s.reshape(-1, 3) if len(s) else np.zeros((0, 3))


def half_breadth(x, z, side=1, tol=6.0):
    """outer half-breadth of hull at (x,z): max side*y of section points within z+-tol (interpolated on segments)."""
    s = slice_axis(x, 0)
    if len(s) == 0:
        return np.nan
    z0, z1 = s[:, 0, 2], s[:, 1, 2]
    m = (np.minimum(z0, z1) <= z) & (np.maximum(z0, z1) >= z)
    if m.sum() == 0:
        return np.nan
    a = s[m]
    t = (z - a[:, 0, 2]) / (a[:, 1, 2] - a[:, 0, 2] + 1e-30)
    y = a[:, 0, 1] + t * (a[:, 1, 1] - a[:, 0, 1])
    return (side * y).max()
