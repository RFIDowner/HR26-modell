"""Head-on bow IMG_9388: silhouette (strake outer edge / hull edge), strake inner edge, boot-top edges, stem."""
import json, numpy as np
from PIL import Image
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
a = np.asarray(Image.open(f"{D}/up/IMG_9388.png").convert("RGB")).astype(float)
L = a.mean(2); R, G, B = a[..., 0], a[..., 1], a[..., 2]
H, W = L.shape
res = {"left": [], "right": [], "bt_top": [], "bt_cream": [], "stem": []}
for v in range(0, 1000, 2):
    row = L[v]
    # left side: scan from x=150 to 700: find first dark strake pixel (L<70) then the hull white after it
    for side, rng in (("left", range(150, 640)), ("right", range(1150, 660, -1))):
        xs = list(rng)
        seg = row[xs]
        dark = np.nonzero(seg < 75)[0]
        if len(dark) == 0:
            continue
        k = dark[0]
        # outer edge of dark band: crossing between background (seg[k-3]) and dark
        ob = xs[k]
        # inner edge: first index after k where seg > 150 (hull white)
        after = np.nonzero(seg[k:] > 150)[0]
        if len(after) == 0:
            continue
        ib = xs[k + after[0]]
        if abs(ib - ob) > 60:
            continue
        res[side].append([v, ob, ib])
# boot-top: for columns 250..1050, top edge = white->dark blue (L drop below 110 coming from >170) between y 480..820
for u in range(250, 1060, 4):
    col = L[450:860, u]; cb = B[450:860, u] - R[450:860, u]
    k = np.nonzero((col[1:] < 110) & (col[:-1] > 140))[0]
    if len(k):
        res["bt_top"].append([u, 450 + k[0] + 0.5])
    # cream line: light (L>150) after the blue band
    if len(k):
        k0 = k[0] + 1
        c = np.nonzero(col[k0 + 5:] > 150)[0]
        if len(c):
            res["bt_cream"].append([u, 450 + k0 + 5 + c[0]])
# stem: the light vertical stripe near x 620..690 between y 0..500: centre of brightest-gradient pair
for v in range(0, 520, 4):
    seg = L[v, 600:700]
    g = np.diff(seg)
    res["stem"].append([v, 600 + int(np.argmin(g)), 600 + int(np.argmax(g))])
json.dump(res, open(f"{D}/m9388.json", "w"), default=float)
Lf = np.array(res["left"]); Rt = np.array(res["right"])
print("left n", len(Lf), "right n", len(Rt))
for v in range(0, 1000, 50):
    i = np.argmin(abs(Lf[:, 0] - v)); j = np.argmin(abs(Rt[:, 0] - v))
    print("v %4d  L outer %4d inner %4d | R outer %4d inner %4d | centre %.1f width %d" % (v, Lf[i, 1], Lf[i, 2], Rt[j, 1], Rt[j, 2], 0.5 * (Lf[i, 1] + Rt[j, 1]), Rt[j, 1] - Lf[i, 1]))
bt = np.array(res["bt_top"]); cr = np.array(res["bt_cream"])
print("bt_top", bt[::10].tolist())
print("cream", cr[::10].tolist())
print("stem", res["stem"][::10])
