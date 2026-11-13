"""At which height z does each stage's hull have the half-breadth of the 448-5 dash-dot line?"""
import sys, json
STAGE, TAG = sys.argv[1], sys.argv[2]
sys.path.insert(0, STAGE)
import numpy as np
from hr26 import params as P, curves as C
tr = json.load(open(r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/out/dashdot_trace.json"))
a = np.array(tr["stb"] + tr["port"]); a[:, 1] = np.abs(a[:, 1])
row = []
for xb in (3500, 3750, 4000, 4250, 4500, 4750, 5000, 5250):
    m = (a[:, 0] >= xb - 60) & (a[:, 0] <= xb + 60)
    if not m.any():
        continue
    y = float(np.median(a[m, 1]))
    p = C._section_geom(float(xb))["pts"]
    mono = np.maximum.accumulate(p[:, 1])
    z = float(np.interp(y, p[:, 0], mono)) if y <= p[:, 0].max() else float("nan")
    # z at which the section reaches y (first crossing)
    zz = None
    for i in range(len(p) - 1):
        if (p[i, 0] - y) * (p[i + 1, 0] - y) <= 0 and p[i + 1, 0] != p[i, 0]:
            t = (y - p[i, 0]) / (p[i + 1, 0] - p[i, 0]); zz = float(p[i, 1] + t * (p[i + 1, 1] - p[i, 1])); break
    row.append((xb, round(y), round(zz) if zz is not None else None))
print(TAG, "x, dash-dot |y|, model z at that half-breadth:", row)
zs = [r[2] for r in row if r[2] is not None]
print(TAG, "mean z %.0f, sd %.0f, range %.0f..%.0f" % (np.mean(zs), np.std(zs), min(zs), max(zs)))
