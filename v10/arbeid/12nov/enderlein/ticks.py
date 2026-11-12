"""Station ticks on the base line between the views, and the plan centreline."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from img import gray, centroid_runs

a = gray()

# base line y between the views
for x in range(400, 2050, 100):
    r = centroid_runs(a[900:960, x], 200)
    print(x, [(round(900 + c, 1), int(m)) for c, s, e, m in r])

# ticks: columns where a vertical dark stroke crosses rows just above/below base line
print("\n-- tick candidates (dark in rows 920-926 and 938-944, i.e. above and below line)")
up = a[918:926, :].min(axis=0)
dn = a[938:946, :].min(axis=0)
cand = np.where((up < 170) & (dn < 200))[0]
groups = []
for x in cand:
    if groups and x - groups[-1][-1] <= 2:
        groups[-1].append(x)
    else:
        groups.append([x])
for g in groups:
    print(round(np.mean(g), 1), len(g), int(up[g].min()), int(dn[g].min()))
