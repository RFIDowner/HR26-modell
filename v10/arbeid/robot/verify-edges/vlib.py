"""Independent verification helpers (numpy only for STL parsing)."""
import math
import struct
import numpy as np

OURS = r"C:/Users/stig/Documents/GitHub/HR26-modell/export/stl/01_skrog.stl"
BAMBU = r"C:/Users/stig/Downloads/Seilbåt fra Bambumotor.stl"
VDIR = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-edges"


def load_stl(path):
    with open(path, "rb") as fh:
        d = fh.read()
    n = struct.unpack("<I", d[80:84])[0]
    assert 84 + 50 * n == len(d), "not a plain binary STL"
    dt = np.dtype([("n", "<f4", (3,)), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec = np.frombuffer(d, dtype=dt, count=n, offset=84)
    return rec["v"].astype(np.float64)


def rot_z(T, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    return T @ R.T


def ours_full(deg=-45.0, T=None):
    """Our hull in full-scale build coordinates: x from bow (bow tip = 4),
    y centred on bbox centre, z above DWL (keel bottom = -1400)."""
    if T is None:
        T = load_stl(OURS)
    T = rot_z(T, deg)
    V = T.reshape(-1, 3)
    xmin, zmin = V[:, 0].min(), V[:, 2].min()
    yc = 0.5 * (V[:, 1].min() + V[:, 1].max())
    out = T.copy()
    out[..., 0] = (T[..., 0] - xmin) * 30.0 + 4.0
    out[..., 1] = (T[..., 1] - yc) * 30.0
    out[..., 2] = (T[..., 2] - zmin) * 30.0 - 1400.0
    return out


def bambu_full(stretch_y=1.0, T=None):
    """Bambu in our full-scale frame: scale 0.3708 (model mm) then x30.
    z: Bambu -37.4 -> our model z 83.1 mm -> full 83.1*30-1400.
    x: Bambu bow-of-hull is aligned later per-call (returned raw-scaled)."""
    if T is None:
        T = load_stl(BAMBU)
    out = T.copy() * 0.3708 * 30.0
    out[..., 1] *= stretch_y
    out[..., 2] = (T[..., 2] + 37.4) * 0.3708 * 30.0 + (83.1 * 30.0 - 1400.0)
    return out


def plane_section(T, axis, val):
    """Intersect triangles with plane coord[axis] = val. Returns (M,2,3) segments."""
    c = T[:, :, axis] - val
    s = np.sign(c)
    s[s == 0] = 1e-12  # treat on-plane as tiny positive
    cross = (s.min(1) < 0) & (s.max(1) > 0)
    P = T[cross]
    cc = c[cross]
    segs = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        ca, cb = cc[:, a], cc[:, b]
        m = (ca * cb) < 0
        t = np.where(m, ca / np.where(m, ca - cb, 1.0), 0.0)
        pts = P[:, a] + t[:, None] * (P[:, b] - P[:, a])
        segs.append((pts, m))
    out = []
    for i in range(len(P)):
        q = [sg[0][i] for sg in segs if sg[1][i]]
        if len(q) >= 2:
            out.append(q[:2])
    return np.array(out)


def chain(segs2d, tol=1e-6):
    """Chain 2D segments (M,2,2) into polylines. Returns list of (K,2) arrays."""
    from collections import defaultdict
    key = lambda p: (round(p[0] / tol) if False else round(float(p[0]), 5), round(float(p[1]), 5))
    adj = defaultdict(list)
    for i, (a, b) in enumerate(segs2d):
        adj[key(a)].append((i, 1))
        adj[key(b)].append((i, 0))
    used = np.zeros(len(segs2d), bool)
    lines = []
    for i0 in range(len(segs2d)):
        if used[i0]:
            continue
        used[i0] = True
        line = [segs2d[i0][0], segs2d[i0][1]]
        for direction in (1, 0):
            while True:
                end = line[-1] if direction == 1 else line[0]
                nxt = None
                for j, e in adj[key(end)]:
                    if not used[j]:
                        nxt = (j, e)
                        break
                if nxt is None:
                    break
                j, e = nxt
                used[j] = True
                other = segs2d[j][e]
                if direction == 1:
                    line.append(other)
                else:
                    line.insert(0, other)
        lines.append(np.array(line))
    return lines


def section_lines(T, axis, val, keep=(1, 2)):
    S = plane_section(T, axis, val)
    if len(S) == 0:
        return []
    S2 = S[:, :, list(keep)]
    return chain(S2)


def fit_line(P):
    c = P.mean(0)
    u, s, vt = np.linalg.svd(P - c)
    return c, vt[0]


def intersect_lines(c1, d1, c2, d2):
    A = np.array([d1, -d2]).T
    t = np.linalg.solve(A, c2 - c1)
    return c1 + t[0] * d1


def dist_point_polyline(p, L):
    a, b = L[:-1], L[1:]
    ab = b - a
    t = np.clip(((p - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0, 1)
    q = a + t[:, None] * ab
    return np.sqrt(((q - p) ** 2).sum(1)).min()
