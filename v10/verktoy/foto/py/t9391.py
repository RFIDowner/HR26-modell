"""Trace IMG_9391 (transom from astern, 1500x2000): strake band, boot-top edges on the transom, rudder centre,
topside silhouettes, red bottom outline."""
import sys; sys.path.insert(0, '.')
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import common as c
a = np.asarray(Image.open(c.FOTO + "/IMG_9391.jpg").convert("RGB")).astype(np.float32)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
L = a.mean(2)
S = R + G + B + 1.0
res = {}

def edge_sub(prof, i0, i1, rising):
    """sub-pixel half-level crossing within [i0,i1) of a 1D profile"""
    p = prof[i0:i1]
    hi, lo = np.percentile(p, 90), np.percentile(p, 10)
    h = 0.5 * (hi + lo)
    s = (p > h) if not rising else (p < h)
    k = np.nonzero(s[:-1] != s[1:])[0]
    if len(k) == 0:
        return np.nan
    k = k[0]
    return i0 + k + (h - p[k]) / (p[k + 1] - p[k] + 1e-9)

# --- boot-top on the transom face: blue band top (white->blue) and bottom (blue->cream), cream->dark below
bt = []
for u in list(range(220, 590, 6)) + list(range(710, 1060, 6)):
    col = ndi.uniform_filter1d(L[:, u - 2:u + 3].mean(1), 3)
    bl = (B - R)[:, u - 2:u + 3].mean(1)          # blue band: B-R high
    rows = np.arange(600, 800)
    isb = bl[600:800] > 25
    if isb.sum() < 15:
        continue
    r = rows[isb]
    top = edge_sub(col, r[0] - 12, r[0] + 8, rising=True)
    bot = edge_sub(col, r[-1] - 6, r[-1] + 10, rising=False)   # blue -> cream (dark->bright)
    # cream -> brown/red: first strong fall after bot
    cr = edge_sub(col, int(bot) + 2, int(bot) + 25, rising=True)
    bt.append([u, top, bot, cr])
res["boottop"] = bt

# --- strake band across the top: dark band, rows 0..140
st = []
for u in list(range(120, 590, 8)) + list(range(710, 1000, 8)):
    col = ndi.uniform_filter1d(L[:200, u - 2:u + 3].mean(1), 3)
    d = col < 0.5 * (np.percentile(col, 95) + np.percentile(col, 5))
    idx = np.nonzero(d[5:160])[0] + 5
    if len(idx) < 5:
        continue
    # largest dark run
    runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
    rr = max(runs, key=len)
    t = edge_sub(col, rr[0] - 6, rr[0] + 4, rising=True)
    b = edge_sub(col, rr[-1] - 4, rr[-1] + 6, rising=False)
    st.append([u, t, b])
res["strake"] = st

# --- rudder: edges of the blade per row (search around u 560..740)
rd = []
for v in range(120, 1560, 10):
    row = ndi.uniform_filter1d(L[v - 2:v + 3, 520:780].mean(0), 3)
    rr = ndi.uniform_filter1d(((R - G) / S)[v - 2:v + 3, 520:780].mean(0), 3)
    rd.append([v, row.tolist() if False else 0])
res["rudder_rows"] = []

# --- red bottom outline (lower silhouette of the hull) rows 740..1000: outermost red pixel connected to the hull red
red = ((R / S) > 0.43) & ((R - G) > 25)
red = ndi.binary_opening(red, iterations=1)
lab, n = ndi.label(red)
cen = lab[860, 640]
main = lab == (cen if cen else np.argmax(np.bincount(lab.ravel())[1:]) + 1)
out = []
for v in range(735, 1010, 2):
    cols = np.nonzero(main[v])[0]
    if len(cols) < 4:
        continue
    out.append([v, float(cols.min()), float(cols.max())])
res["red_outline"] = out
c.save_json(res, c.W + "/out/t9391.json")
print("boottop n", len(bt), bt[::10])
print("strake n", len(st), st[::8])
print("red", out[::10])
