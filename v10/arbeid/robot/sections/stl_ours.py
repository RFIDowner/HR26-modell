"""Slice our STL (01_skrog.stl) at stations, compare with formula and OCC spline. Full-scale mm."""
import sys, struct, math, json
import numpy as np
sys.path.insert(0, r"C:/Users/stig/Documents/GitHub/HR26-modell")
from hr26 import curves as C, params as P

OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/sections"
FR = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]


def load(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
    return rec["v"].astype(np.float64)


def rotz(T, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return T @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T


def slice_x(T, x0):
    X = T[:, :, 0]
    sel = (X.min(1) < x0) & (X.max(1) > x0)
    Pp = T[sel]
    out = []
    pts = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        A, B = Pp[:, a], Pp[:, b]
        cr = (A[:, 0] - x0) * (B[:, 0] - x0) < 0
        t = np.where(cr, (x0 - A[:, 0]) / np.where(cr, B[:, 0] - A[:, 0], 1), 0)
        pts.append(((A + t[:, None] * (B - A))[:, 1:], cr))
    segs = []
    for i in range(len(Pp)):
        q = [p[0][i] for p in pts if p[1][i]]
        if len(q) == 2:
            segs.append(q)
    return np.array(segs)  # (M,2,2) (y,z)


def outer_rays(segs, c, angs):
    a = segs[:, 0]; b = segs[:, 1]; d = b - a
    res = []
    for th in angs:
        r = np.array([math.cos(th), math.sin(th)])
        den = r[0] * d[:, 1] - r[1] * d[:, 0]
        ok = np.abs(den) > 1e-12
        w = a - c
        t = np.where(ok, (w[:, 0] * d[:, 1] - w[:, 1] * d[:, 0]) / np.where(ok, den, 1), -1)
        s = np.where(ok, (w[:, 0] * r[1] - w[:, 1] * r[0]) / np.where(ok, den, 1), -1)
        hit = ok & (t > 0) & (s >= 0) & (s <= 1)
        if hit.any():
            tt = t[hit].max()
            res.append(c + tt * r)
    return np.array(res)


def normal_dev(test, ref):
    sa, sb = ref[:-1], ref[1:]
    d = sb - sa; L2 = (d ** 2).sum(1)
    res = []
    for p in test:
        t = np.clip(((p - sa) * d).sum(1) / np.maximum(L2, 1e-12), 0, 1)
        q = sa + t[:, None] * d
        dist = np.hypot(*(p - q).T)
        j = int(np.argmin(dist))
        nrm = np.array([d[j, 1], -d[j, 0]]) / math.sqrt(L2[j])
        res.append(np.sign(((p - q[j]) * nrm).sum()) * dist[j])
    return np.array(res)


T = load(r"C:/Users/stig/Documents/GitHub/HR26-modell/export/stl/01_skrog.stl")
V = T.reshape(-1, 3)
T = rotz(T, -45.0)
yc = (T[:, :, 1].max() + T[:, :, 1].min()) / 2
T[:, :, 1] -= yc
xmin = T[:, :, 0].min()
# to full scale: x from bow (bow tip = first loft station x=4), z from DWL
F = T.copy()
F[:, :, 0] = (T[:, :, 0] - xmin) * P.SCALE + 4.0
F[:, :, 1] = T[:, :, 1] * P.SCALE
F[:, :, 2] = T[:, :, 2] * P.SCALE - P.DRAFT
np.save(OUT + "/ours_fullscale_tris.npy", F.astype(np.float32))


def contour(x):
    segs = slice_x(F, x)
    zb, zs = C.bottom_z(x), C.sheer_z(x)
    c = np.array([0.0, 0.5 * (min(zb, 0.0) + zs) if zb < 0 else 0.5 * (zb + zs)])
    angs = np.radians(np.linspace(-89.5, 89.0, 3000))
    pts = outer_rays(segs, c, angs)
    pts = pts[(pts[:, 0] > 2.0) & (pts[:, 1] <= zs - 5.0)]
    return segs, pts


def masks(x, pts):
    zk, zs = C.strake_z(x), C.sheer_z(x)
    m = np.ones(len(pts), bool)
    m &= ~((pts[:, 1] > zk - 47.5 - 25) & (pts[:, 1] < zk + 47.5 + 25))      # strake
    if P.WIN_X0 - 60 <= x <= P.WIN_X1 + 60:
        m &= ~((pts[:, 1] > zk + P.WIN_ABOVE_STRAKE - 30) & (pts[:, 1] < zs - P.WIN_BELOW_DECK + 30))  # window
    if P.KEEL_LE_ROOT - 150 <= x <= P.KEEL_TE_ROOT + 150:
        m &= pts[:, 0] > P.KEEL_ROOT_T / 2 + P.KEEL_FILLET + 60                # keel root + fillet
    return m


rows = []
store = {}
for f in FR:
    x = f * P.LOA
    segs, pts = contour(x)
    m = masks(x, pts)
    an = np.array(C.section(x, n=8000))
    dev = normal_dev(pts, an)
    Z = pts[:, 1]
    zs = C.sheer_z(x)
    r = dict(f=f, x=round(x))
    for nm, sel in (("below", (Z < -60) & m), ("dwl", (np.abs(Z) <= 60) & m), ("top", (Z > 60) & m)):
        if sel.sum() > 3:
            r[nm + "_max"] = round(float(dev[sel].max()), 1); r[nm + "_min"] = round(float(dev[sel].min()), 1)
            r[nm + "_rms"] = round(float(np.sqrt((dev[sel] ** 2).mean())), 1)
    # straightness of STL topside (DWL -> deck edge chord), excluding strake/window
    top = (Z >= 0) & m
    if top.sum() > 5 and C.bottom_z(x) < -1:
        y0 = float(np.interp(0.0, Z[np.argsort(Z)], pts[np.argsort(Z), 0]))
        bd = C.deck_half_breadth(x)
        cy, cz = bd - y0, zs
        L = math.hypot(cy, cz); nrm = np.array([cz, -cy]) / L
        dv = (pts[top, 0] - y0) * nrm[0] + (Z[top]) * nrm[1]
        r["stl_topside_dev"] = round(float(dv[np.argmax(np.abs(dv))]), 1)
        r["stl_y_at_dwl"] = round(y0, 1)
    rows.append(r)
    store[f] = dict(pts=pts.tolist(), m=m.tolist())

for k in rows[0].keys() | set().union(*[r.keys() for r in rows]):
    pass
keys = ["f", "x", "below_max", "below_min", "below_rms", "dwl_max", "dwl_min", "dwl_rms", "top_max", "top_min", "top_rms", "stl_topside_dev", "stl_y_at_dwl"]
for k in keys:
    print(f"{k:>16s}: " + " | ".join(str(r.get(k, "-")) for r in rows))
json.dump(store, open(OUT + "/ours_contours.json", "w"))

# loft interpolation: midpoints between loft stations
xs = C.stations(40)
xs = [x for x in xs if 6.0 < x < P.LOA - 4.0]
xs = sorted(set([4.0] + xs + [7850.0, 7910.0] + [P.LOA - 2.0]))
xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 8.0]
print("\nloft-station vs midpoint deviation (STL minus formula, full-scale mm; strake/window/keel masked)")
print(f"{'x':>6} {'type':>5} {'below max/min':>16} {'|z|<60 max/min':>16} {'top max/min':>16}")
for i in range(1, len(xs) - 3):
    for x, typ in ((xs[i], "stat"), (0.5 * (xs[i] + xs[i + 1]), "mid")):
        if x < 300 or x > 7700:
            continue
        segs, pts = contour(x)
        m = masks(x, pts)
        an = np.array(C.section(x, n=8000))
        dev = normal_dev(pts[::2], an); Z = pts[::2, 1]; mm = m[::2]
        out = []
        for sel in ((Z < -60) & mm, (np.abs(Z) <= 60) & mm, (Z > 60) & mm):
            out.append(f"{dev[sel].max():6.1f}/{dev[sel].min():6.1f}" if sel.sum() > 2 else "      -      ")
        print(f"{x:6.0f} {typ:>5} {out[0]:>16} {out[1]:>16} {out[2]:>16}")
