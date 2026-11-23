"""Small numpy-only STL helpers (own implementation)."""
import struct, math
import numpy as np

def load_stl(path):
    with open(path, "rb") as fh:
        d = fh.read()
    n = struct.unpack("<I", d[80:84])[0]
    if 84 + 50 * n != len(d):
        raise ValueError(f"not a clean binary STL: n={n}, size={len(d)}")
    dt = np.dtype([("n", "<f4", (3,)), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec = np.frombuffer(d, dtype=dt, count=n, offset=84)
    return rec["v"].astype(np.float64)          # (n,3,3)

def rot_z(T, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
    return T @ R.T

def slice_x(T, x0):
    """segments (k,2,2) in (y,z) where plane x=x0 cuts triangles"""
    X = T[:, :, 0]
    sel = (X.min(1) < x0) & (X.max(1) > x0)
    P = T[sel]
    if len(P) == 0:
        return np.zeros((0, 2, 2))
    pts = []
    flags = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        A, B = P[:, a], P[:, b]
        cr = (A[:, 0] - x0) * (B[:, 0] - x0) < 0
        den = np.where(cr, B[:, 0] - A[:, 0], 1.0)
        t = np.where(cr, (x0 - A[:, 0]) / den, 0.0)
        pts.append((A + t[:, None] * (B - A))[:, 1:])
        flags.append(cr)
    pts = np.stack(pts, 1)          # (k,3,2)
    flags = np.stack(flags, 1)      # (k,3)
    ok = flags.sum(1) == 2
    pts, flags = pts[ok], flags[ok]
    idx = np.argsort(~flags, axis=1, kind="stable")[:, :2]
    seg = np.take_along_axis(pts, idx[:, :, None], axis=1)
    return seg

def outer_y_of_z(seg, zgrid, side=+1):
    """max (side*y) of the cut at each z in zgrid (outer skin), NaN if none.
    Uses the segment crossings with the horizontal line z."""
    out = np.full(len(zgrid), np.nan)
    if len(seg) == 0:
        return out
    y0, z0 = seg[:, 0, 0], seg[:, 0, 1]
    y1, z1 = seg[:, 1, 0], seg[:, 1, 1]
    zlo = np.minimum(z0, z1); zhi = np.maximum(z0, z1)
    for i, z in enumerate(zgrid):
        m = (zlo <= z) & (zhi > z) & (zhi - zlo > 1e-12)
        if not m.any():
            continue
        t = (z - z0[m]) / (z1[m] - z0[m])
        y = y0[m] + t * (y1[m] - y0[m])
        v = (side * y).max()
        out[i] = side * v
    return out
