"""Sheet geometry: frame border lines, folds, station ticks, plan centreline.
Checks rotation and scale uniformity of the scan."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from img import gray, centroid_runs

a = gray()
H, W = a.shape
print("size", W, H)


def line_y(x, y0, y1, thr=170):
    col = a[y0:y1, x]
    r = centroid_runs(col, thr)
    if not r:
        return None
    # darkest run
    r.sort(key=lambda t: t[3])
    return y0 + r[0][0]


def line_x(y, x0, x1, thr=170):
    row = a[y, x0:x1]
    r = centroid_runs(row, thr)
    if not r:
        return None
    r.sort(key=lambda t: t[3])
    return x0 + r[0][0]


print("\n-- top border y(x)")
xs = list(range(80, 2540, 120))
top = [(x, line_y(x, 10, 80)) for x in xs]
print(" ".join(f"{x}:{y:.1f}" for x, y in top if y is not None))
print("-- bottom border y(x)")
bot = [(x, line_y(x, 1720, 1772)) for x in xs]
print(" ".join(f"{x}:{y:.1f}" for x, y in bot if y is not None))
ys = list(range(80, 1740, 80))
print("-- left border x(y)")
lef = [(y, line_x(y, 10, 80)) for y in ys]
print(" ".join(f"{y}:{x:.1f}" for y, x in lef if x is not None))
print("-- right border x(y)")
rig = [(y, line_x(y, 2500, 2560)) for y in ys]
print(" ".join(f"{y}:{x:.1f}" for y, x in rig if x is not None))


def fit(pairs):
    p = np.array([(u, v) for u, v in pairs if v is not None], float)
    c = np.polyfit(p[:, 0], p[:, 1], 1)
    res = p[:, 1] - np.polyval(c, p[:, 0])
    return c, res


for name, pr in (("top", top), ("bottom", bot), ("left", lef), ("right", rig)):
    c, res = fit(pr)
    print(f"{name}: slope {c[0]*1000:.3f} px/1000px  ({np.degrees(np.arctan(c[0])):.4f} deg)  "
          f"intercept {c[1]:.1f}  resid max {np.abs(res).max():.2f} rms {res.std():.2f}")
