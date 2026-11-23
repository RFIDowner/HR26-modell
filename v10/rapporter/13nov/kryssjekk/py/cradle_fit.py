"""Does the hull between x-90 and x+90 (the cradle slab, STAND_THICK 180 full)
stay inside the cradle's cut-out, which stand.py makes from ONE station
section (offset outward by CLEAR = 7.5 mm)? Reports the worst penetration of
the hull into the cradle (mm, full scale) per stage and cradle.

usage: python cradle_fit.py <stage_dir> <tag> [param overrides as json]
"""
import sys, json, importlib
STAGE, TAG = sys.argv[1], sys.argv[2]
sys.path.insert(0, STAGE)
import numpy as np
from matplotlib.path import Path
from hr26 import params as P, curves as C
if len(sys.argv) > 3:
    for k, v in json.loads(sys.argv[3]).items():
        setattr(P, k, v)
    C = importlib.reload(sys.modules["hr26.curves"])
import math

CLEAR = 0.25 * P.SCALE


def offset_section(x, clear, n=30):
    pts = C.section(x, n=n)
    pts = pts + [(y, z) for (y, z) in C.deck_arc(x)[1:]]
    out = []
    for i, (y, z) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        ty, tz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ty, tz) or 1.0
        out.append((y + tz / L * clear, z - ty / L * clear))
    return out


def seg_dist(p, poly):
    a = poly[:-1]; b = poly[1:]
    ab = b - a; ap = p[None, :] - a
    t = np.clip((ap * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-12), 0, 1)
    d = a + t[:, None] * ab - p[None, :]
    return float(np.sqrt((d * d).sum(1)).min())


out = {}
for xs in P.STAND_STATIONS:
    prof = offset_section(xs, CLEAR)
    stb = np.array(prof)
    poly = np.vstack([stb, (stb * [-1, 1])[::-1], stb[:1]])
    path = Path(poly)
    zb = C.bottom_z(xs); top = zb + 0.55 * (C.sheer_z(xs) - zb)
    worst = (0.0, None)
    for x in np.linspace(xs - 0.5 * P.STAND_THICK, xs + 0.5 * P.STAND_THICK, 13):
        sec = np.array(C.section(float(x), 160), float)
        sec = sec[sec[:, 1] <= top]
        for p in sec:
            if not path.contains_point(p):
                d = seg_dist(p, poly)
                if d > worst[0]:
                    worst = (d, (round(float(x)), round(float(p[0])), round(float(p[1]))))
    out[xs] = dict(max_penetration_mm=round(worst[0], 1), where_x_y_z=worst[1])
print(TAG, json.dumps(out))
