import sys, json; sys.path.insert(0, '.')
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import common as c
a = np.asarray(Image.open(c.FOTO + "/IMG_9388.jpg").convert("RGB")).astype(np.float32)
a = ndi.gaussian_filter(a, (1.0, 1.0, 0))
R, G, B = a[..., 0], a[..., 1], a[..., 2]
L = a.mean(2)
out = []
for u in list(range(200, 640, 8)) + list(range(684, 1120, 8)):
    blue = (B[:, u] - R[:, u]) > 18
    rows = np.nonzero(blue[480:960])[0] + 480
    if len(rows) < 10:
        continue
    runs = np.split(rows, np.nonzero(np.diff(rows) > 3)[0] + 1)
    rr = max(runs, key=len)
    if len(rr) < 10:
        continue
    b_end = rr[-1]
    col = L[:, u]
    # cream: bright peak within 30 px below the blue end; cream lower edge = half-level crossing after the peak
    seg = col[b_end:b_end + 40]
    k = int(np.argmax(seg)); peak = seg[k]
    below = col[b_end + k:b_end + k + 30]
    lowv = np.percentile(below, 10)
    h = 0.5 * (peak + lowv)
    j = np.nonzero(below < h)[0]
    if len(j) == 0 or peak < 120:
        continue
    j = j[0]
    vc = b_end + k + j - 1 + (below[j - 1] - h) / (below[j - 1] - below[j] + 1e-9)
    out.append([u, float(rr[0]), float(b_end), float(vc)])
c.save_json(out, c.W + "/out/bt9388.json")
im = Image.open(c.FOTO + "/IMG_9388.jpg").convert("RGB"); d = ImageDraw.Draw(im)
for u, t, b, vc in out:
    d.ellipse([u - 2, vc - 2, u + 2, vc + 2], outline=(0, 255, 0)); d.point((u, t), fill=(255, 255, 0))
im.crop((150, 450, 1150, 1000)).save(c.W + "/img/bt9388_chk.png")
print(len(out), [(o[0], round(o[3], 1)) for o in out[::6]])
