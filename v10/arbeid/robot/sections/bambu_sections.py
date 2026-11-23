"""Read the UNTRUSTED Bambu STL with numpy only (run with python -I). Align to our hull, slice stations,
save outer starboard contours (full-scale mm) for later analysis. No code from Downloads is executed."""
import struct, math, json, sys
import numpy as np

OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/sections"
BAMBU = sys.argv[1]
SCALE = 30.0


def load(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    assert 84 + 50 * n == len(d), "not a plain binary STL"
    rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
    return rec["v"].astype(np.float64)


def frame(T):
    """as compare.py: z of max beam in the middle part, bow x and length at that height"""
    V = T.reshape(-1, 3)
    B = np.ptp(V[:, 1])
    x0, x1 = np.percentile(V[:, 0], [30, 70])
    mid = V[(V[:, 0] > x0) & (V[:, 0] < x1)]
    zb = np.round(mid[:, 2] / (B * 0.01)).astype(int)
    best = max(set(zb.tolist()), key=lambda k: np.abs(mid[zb == k, 1]).max())
    z_mb = best * B * 0.01
    band = V[(V[:, 2] > z_mb - 0.12 * B) & (V[:, 2] <= z_mb + 0.01 * B)]
    xb = np.floor((band[:, 0] - band[:, 0].min()) / (B * 0.01)).astype(int)
    env = np.zeros(xb.max() + 1); np.maximum.at(env, xb, np.abs(band[:, 1]))
    wide = np.nonzero(env > 0.25 * B / 2)[0]
    x_bow = band[:, 0].min(); x_st = band[:, 0].min() + (wide.max() + 1) * B * 0.01
    return dict(B=B, L=x_st - x_bow, x_bow=x_bow, z_mb=z_mb)


def rotz(T, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return T @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T


def slice_x(T, x0):
    X = T[:, :, 0]
    sel = (X.min(1) < x0) & (X.max(1) > x0)
    Pp = T[sel]
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
    return np.array(segs)


# ours, model mm, correct plate rotation 45 deg
ours = load(r"C:/Users/stig/Documents/GitHub/HR26-modell/export/stl/01_skrog.stl")
ours = rotz(ours, -45.0)
ours[:, :, 1] -= (ours[:, :, 1].max() + ours[:, :, 1].min()) / 2
fo = frame(ours)
bam = load(BAMBU)
fb = frame(bam)
s = fo["L"] / fb["L"]
print("ours frame", {k: round(v, 3) for k, v in fo.items()})
print("bambu frame", {k: round(v, 3) for k, v in fb.items()}, "scale", round(s, 4), "beam ratio", round(fb["B"] * s / fo["B"], 4))
x_tip_ours = ours[:, :, 0].min()
yc_b = 0.5 * (bam[:, :, 1].max() + bam[:, :, 1].min())
Ystretch = fo["B"] / (fb["B"] * s)
print("y stretch", round(Ystretch, 4))
# Bambu -> our model mm -> our full scale (x from bow tip = 4, z from DWL)
Bm = bam.copy()
Bm[:, :, 0] = (bam[:, :, 0] - fb["x_bow"]) * s + fo["x_bow"]
Bm[:, :, 1] = (bam[:, :, 1] - yc_b) * s
Bm[:, :, 2] = (bam[:, :, 2] - fb["z_mb"]) * s + fo["z_mb"]
BF = Bm.copy()
BF[:, :, 0] = (Bm[:, :, 0] - x_tip_ours) * SCALE + 4.0
BF[:, :, 1] = Bm[:, :, 1] * SCALE                     # raw width (not stretched)
BF[:, :, 2] = Bm[:, :, 2] * SCALE - 1400.0
print("bambu full-scale extents x", BF[:, :, 0].min().round(0), BF[:, :, 0].max().round(0), " z", BF[:, :, 2].min().round(0), BF[:, :, 2].max().round(0))
print("bambu z_mb full-scale", round(fo["z_mb"] * SCALE - 1400, 0), " (bambu z_mb raw", round(fb["z_mb"], 2), ")")

FR = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
LOA = 7950.0
res = {"stretch": Ystretch, "scale": s, "z_mb_full": fo["z_mb"] * SCALE - 1400}
for f in FR:
    x = f * LOA
    segs = slice_x(BF, x)
    if len(segs) == 0:
        continue
    P_ = segs.reshape(-1, 2)
    # bottom of the hull at the centreline and hull outer starboard envelope (max y per z bin)
    zbins = np.arange(np.floor(P_[:, 1].min() / 10) * 10, P_[:, 1].max() + 10, 10.0)
    env = []
    for z0 in zbins:
        sel = (np.abs(P_[:, 1] - z0) <= 5) & (P_[:, 0] > 0)
        if sel.sum():
            env.append((float(P_[sel, 0].max()), float(z0)))
    # bottom: min z per y bin (starboard)
    ybins = np.arange(0, P_[:, 0].max() + 10, 10.0)
    bot = []
    for y0 in ybins:
        sel = np.abs(P_[:, 0] - y0) <= 5
        if sel.sum():
            bot.append((float(y0), float(P_[sel, 1].min())))
    res[str(f)] = dict(x=x, env=env, bottom=bot, segs=segs.tolist())
json.dump(res, open(OUT + "/bambu_sections.json", "w"))
print("saved", len(res) - 3, "stations")
