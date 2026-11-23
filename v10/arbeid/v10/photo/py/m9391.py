"""Transom IMG_9391: strake band across transom, boot-top edges, hull silhouette (right side vs sky), rudder."""
import sys, json, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/py")
from track import track
from PIL import Image
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
a = np.asarray(Image.open(f"{D}/up/IMG_9391.png").convert("RGB")).astype(float)
L = a.mean(2); R, G, B = a[..., 0], a[..., 1], a[..., 2]
res = {}
# strake across transom: dark band; track from (300, 68)
S = track(L, 300, 68, 0, 1300, win=5, maxjump=2.5)
res["strake"] = S.tolist()
print("strake n", len(S), "u range", S[0, 0], S[-1, 0])
for u in (0, 50, 100, 200, 300, 400, 500, 560, 700, 800, 900, 1000, 1100, 1150, 1200, 1230, 1260):
    i = np.argmin(abs(S[:, 0] - u)); r = S[i]; print("  u %4d top %.1f bot %.1f ctr %.1f thick %.1f" % (r[0], r[1], r[2], r[3], r[2] - r[1]))
# boot-top top edge: white -> dark blue, columns 150..1120, rows 600..760
bt = []
for u in range(140, 1130, 2):
    col = L[600:770, u]
    k = np.nonzero((col[1:] < 100) & (col[:-1] > 120))[0]
    if len(k):
        k = k[0]; hi = col[max(k - 4, 0):k + 1].max(); lo = col[k + 1:k + 5].min(); half = 0.5 * (hi + lo)
        kk = k
        while kk + 1 < len(col) and col[kk + 1] > half:
            kk += 1
        t = kk + (col[kk] - half) / (col[kk] - col[kk + 1] + 1e-9)
        # cream stripe below: first row after +8 with L>150
        c = np.nonzero(col[kk + 8:] > 150)[0]
        cr = 600 + kk + 8 + c[0] if len(c) else np.nan
        bt.append([u, 600 + t, cr])
bt = np.array(bt); res["boottop"] = bt.tolist()
for u in (160, 200, 250, 300, 400, 500, 560, 700, 800, 900, 1000, 1050, 1100):
    i = np.argmin(abs(bt[:, 0] - u)); print("  bt u %4d top %.1f cream %.1f" % tuple(bt[i]))
# right silhouette: for rows 150..760, rightmost hull pixel: scan from x=1400 leftwards, first pixel with white hull (L>150, low sat) after sky
sil = []
for v in range(120, 760, 4):
    row = L[v]; sat = a[v].max(1) - a[v].min(1)
    hull = (row > 140) & (sat < 40)
    # find run from 900..1350
    xs = np.arange(900, 1350)
    hh = hull[900:1350]
    # rightmost x where hull True and the next 6 px are mostly non-hull (sky: bluish sat>20 or brighter)
    idx = np.nonzero(hh)[0]
    if len(idx) == 0:
        continue
    sil.append([v, 900 + idx.max()])
res["sil_right"] = sil
print("sil right", sil[::10])
json.dump(res, open(f"{D}/m9391.json", "w"), default=float)
