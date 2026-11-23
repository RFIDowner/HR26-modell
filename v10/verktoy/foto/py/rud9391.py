import sys; sys.path.insert(0, '.')
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import common as c
a = np.asarray(Image.open(c.FOTO + "/IMG_9391.jpg").convert("RGB")).astype(np.float32)
a = ndi.gaussian_filter(a, (1.0, 1.0, 0))
R, G, B = a[..., 0], a[..., 1], a[..., 2]
pink = (R > 120) & ((R - G) > 50) & (R > 1.25 * B)
out = []
for v in range(770, 1560, 10):
    row = pink[v, 520:800]
    idx = np.nonzero(row)[0]
    if len(idx) < 20:
        continue
    runs = np.split(idx, np.nonzero(np.diff(idx) > 2)[0] + 1)
    rr = max(runs, key=len)
    l, r = 520 + rr[0], 520 + rr[-1]
    out.append([v, float(l), float(r)])
c.save_json(out, c.W + "/out/rud9391.json")
print([(o[0], o[1], o[2], o[2] - o[1]) for o in out[::6]])
