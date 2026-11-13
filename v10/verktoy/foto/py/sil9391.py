import sys; sys.path.insert(0, '.')
import json, numpy as np
from PIL import Image
from scipy import ndimage as ndi
import common as c
a = np.asarray(Image.open(c.FOTO + "/IMG_9391.jpg").convert("RGB")).astype(np.float32)
a = ndi.gaussian_filter(a, (1.5, 1.5, 0))
gx = np.sqrt(sum(ndi.sobel(a[..., k], axis=1) ** 2 for k in range(3)))
guessR = [(260, 1222), (300, 1214), (350, 1206), (400, 1197), (450, 1188), (500, 1180), (550, 1166), (600, 1153), (640, 1140)]
guessL = [(480, 35), (520, 45), (560, 55), (600, 72), (640, 95), (680, 128), (700, 148)]
out = {"right": [], "left": []}
for key, gs in (("right", guessR), ("left", guessL)):
    gs = np.array(gs, float)
    for v in range(int(gs[0, 0]), int(gs[-1, 0]) + 1, 10):
        ug = np.interp(v, gs[:, 0], gs[:, 1])
        lo, hi = int(max(ug - 30, 1)), int(ug + 30)
        g = gx[v, lo:hi]
        k = int(np.argmax(g))
        if 0 < k < len(g) - 1:
            d = 0.5 * (g[k - 1] - g[k + 1]) / (g[k - 1] - 2 * g[k] + g[k + 1] + 1e-9)
        else:
            d = 0.0
        out[key].append([v, lo + k + d, float(g[k])])
c.save_json(out, c.W + "/out/sil9391.json")
for k in out:
    print(k, [(r[0], round(r[1], 1), int(r[2])) for r in out[k]])
