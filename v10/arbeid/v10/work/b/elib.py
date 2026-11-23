"""Helpers for the edge analysis (own scratch code; reads STL with numpy only)."""
import math, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OURS = "C:/Users/stig/Documents/GitHub/HR26-modell/export/stl/01_skrog.stl"
BAMBU = "C:/Users/stig/Downloads/Seilbåt fra Bambumotor.stl"
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b"
S = 30.0           # scale
DRAFT = 1400.0


def load(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]),
                        count=n, offset=84)
    return rec["v"].astype(np.float64)


def rotz(T, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return T @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T


def ours_full(x_first=4.0):
    """Our hull in full-scale build coordinates: x from bow, y half-breadth, z above DWL.
    x is anchored so the foremost point = first loft station (x=4 mm)."""
    T = rotz(load(OURS), -45.0)   # NB: 45, not 44 (verified by symmetry of mast hole, cleats, roller)
    V = T.reshape(-1, 3)
    T[:, :, 1] -= 0.5 * (V[:, 1].max() + V[:, 1].min())
    T[:, :, 0] -= V[:, 0].min()
    T *= S
    T[:, :, 0] += x_first
    T[:, :, 2] -= DRAFT
    return T


def bambu_full(stretch_y=True, k=0.3708, zb_ref=-37.4, zo_ref_model=83.1, x_bow_full=None):
    """Bambu mesh in our full-scale frame. Scaled k to our model mm, z aligned at the
    max-beam height, optionally y stretched 1.223 for shape comparisons."""
    T = load(BAMBU)
    T = T * k
    T[:, :, 2] = T[:, :, 2] - zb_ref * k + zo_ref_model
    if stretch_y:
        T[:, :, 1] *= 1.223
    T *= S
    T[:, :, 2] -= DRAFT
    return T


def section(T, axis, c):
    """Intersect triangles with plane coord[axis]=c. Returns segments (M,2,3)."""
    A = T[:, :, axis]
    sel = (A.min(1) < c) & (A.max(1) > c)
    P = T[sel]
    out = []
    pts = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        pa, pb = P[:, a], P[:, b]
        da, db = pa[:, axis] - c, pb[:, axis] - c
        cr = da * db < 0
        t = np.where(cr, da / np.where(cr, da - db, 1.0), 0.0)
        pts.append((pa + t[:, None] * (pb - pa), cr))
    segs = []
    for i in range(len(P)):
        q = [p[0][i] for p in pts if p[1][i]]
        if len(q) == 2:
            segs.append(q)
    return np.array(segs)


def chain(segs, tol=1e-3):
    """Chain segments (M,2,D) into polylines by matching rounded endpoints."""
    from collections import defaultdict
    key = lambda p: tuple(np.round(p / tol).astype(np.int64))
    adj = defaultdict(list)
    for i, (a, b) in enumerate(segs):
        adj[key(a)].append((i, 0))
        adj[key(b)].append((i, 1))
    used = np.zeros(len(segs), bool)
    lines = []
    for i0 in range(len(segs)):
        if used[i0]:
            continue
        used[i0] = True
        line = [segs[i0][0], segs[i0][1]]
        # extend forward
        for direction in (1, 0):
            while True:
                end = line[-1] if direction == 1 else line[0]
                nxt = None
                for (j, e) in adj[key(end)]:
                    if not used[j]:
                        nxt = (j, e); break
                if nxt is None:
                    break
                j, e = nxt
                used[j] = True
                p = segs[j][1 - e]
                if direction == 1:
                    line.append(p)
                else:
                    line.insert(0, p)
        lines.append(np.array(line))
    return lines


def turning_profile(P):
    """Arc length and cumulative signed turning angle along a 2-D polyline P (n,2)."""
    d = np.diff(P, axis=0)
    L = np.hypot(d[:, 0], d[:, 1])
    keep = L > 1e-9
    d, L = d[keep], L[keep]
    ang = np.arctan2(d[:, 1], d[:, 0])
    dang = np.diff(ang)
    dang = (dang + np.pi) % (2 * np.pi) - np.pi
    s_mid = np.concatenate([[0], np.cumsum(L)])           # at vertices
    # turning happens at interior vertices 1..n-2
    return s_mid[1:-1], np.cumsum(dang), ang, L


def eff_radius(P, frac=(0.1, 0.9)):
    """Effective radius of a corner: arc length over which the central part of the total
    turning happens, divided by that angle. P must run across one corner only."""
    s, cum, ang, L = turning_profile(P)
    tot = cum[-1]
    if abs(tot) < 1e-6:
        return float('nan'), 0.0
    f = cum / tot
    i0 = np.searchsorted(f, frac[0]); i1 = np.searchsorted(f, frac[1])
    i0 = min(max(i0, 0), len(s) - 1); i1 = min(max(i1, 0), len(s) - 1)
    ds = s[i1] - s[i0]
    dth = abs(cum[i1] - (cum[i0 - 1] if i0 > 0 else 0.0))
    if dth < 1e-6:
        return 0.0, math.degrees(tot)
    return ds / dth, math.degrees(tot)


def font(sz):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", sz)
    except Exception:
        return ImageFont.load_default()


def shade_view(T, M, W, box=None, light=(0.35, -0.55, 0.75), bg=(255, 255, 255), col=(1.0, 1.0, 1.06),
               H=None):
    """Flat-shaded orthographic render. M is a 3x3 matrix mapping world to (u, v, depth)
    with u right, v up, depth towards viewer positive. box=(umin,umax,vmin,vmax)."""
    P = T @ M.T
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    nl = np.array(light, float); nl /= np.linalg.norm(nl)
    lw = nl  # light in world coordinates
    sh = np.clip(np.abs(n @ lw), 0, 1) * 0.72 + 0.22
    U, Vv, D = P[:, :, 0], P[:, :, 1], P[:, :, 2].mean(1)
    if box is None:
        box = (U.min(), U.max(), Vv.min(), Vv.max())
    umin, umax, vmin, vmax = box
    sel = (U.max(1) >= umin) & (U.min(1) <= umax) & (Vv.max(1) >= vmin) & (Vv.min(1) <= vmax)
    sc = W / (umax - umin)
    if H is None:
        H = int((vmax - vmin) * sc)
    img = Image.new("RGB", (W, H), bg)
    dr = ImageDraw.Draw(img)
    idx = np.nonzero(sel)[0]
    idx = idx[np.argsort(D[idx])]
    PU = (U - umin) * sc
    PV = H - (Vv - vmin) * sc
    for i in idx:
        g = sh[i] * 255
        dr.polygon([(PU[i, 0], PV[i, 0]), (PU[i, 1], PV[i, 1]), (PU[i, 2], PV[i, 2])],
                   fill=(int(g * col[0]), int(g * col[1]), min(255, int(g * col[2]))))
    return img, sc


def view_matrix(az, el):
    """Camera: azimuth az (deg) about z, elevation el (deg). Returns M (u, v, depth)."""
    a, e = math.radians(az), math.radians(el)
    # view direction from camera towards target
    d = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), -math.sin(e)])
    up = np.array([0, 0, 1.0])
    u = np.cross(d, up); u /= np.linalg.norm(u)
    v = np.cross(u, d)
    return np.array([u, v, -d])
