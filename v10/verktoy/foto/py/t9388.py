"""IMG_9388 lower underwater outline (V bottom) by columns, plus bilge rows by rows."""
import sys, json; sys.path.insert(0, '.')
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import common as c
a = np.asarray(Image.open(c.FOTO + "/IMG_9388.jpg").convert("RGB")).astype(np.float32)
a = ndi.gaussian_filter(a, (1.2, 1.2, 0))
R, G, B = a[..., 0], a[..., 1], a[..., 2]
S = R + G + B + 1
red = ((R / S) > 0.45) & ((R - G) > 30) & ((G / S) < 0.27)
red = ndi.binary_opening(red, iterations=1)
lab, n = ndi.label(red)
main = lab == lab[900, 650]
cols = []
for u in range(330, 980, 6):
    rr = np.nonzero(main[860:1060, u])[0]
    if len(rr) == 0:
        continue
    cols.append([u, 860 + rr.max() + 0.5])
rows = []
for v in range(840, 960, 4):
    cc = np.nonzero(main[v, 150:1150])[0]
    if len(cc) == 0:
        continue
    rows.append([v, 150 + cc.min() - 0.5, 150 + cc.max() + 0.5])
c.save_json(dict(bottom_cols=cols, side_rows=rows), c.W + "/out/t9388.json")
im = Image.open(c.FOTO + "/IMG_9388.jpg").convert("RGB"); d = ImageDraw.Draw(im)
for u, v in cols:
    d.ellipse([u - 3, v - 3, u + 3, v + 3], outline=(0, 255, 0))
for v, l, r in rows:
    d.ellipse([l - 3, v - 3, l + 3, v + 3], outline=(0, 255, 255)); d.ellipse([r - 3, v - 3, r + 3, v + 3], outline=(0, 255, 255))
im.crop((150, 700, 1150, 1100)).save(c.W + "/img/t9388_chk.png")
print(cols[::5]); print(rows[::5])
