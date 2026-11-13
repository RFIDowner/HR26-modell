"""Hoeydereferansen i IMG_9391 (13.11.2026 kveld).

Kameraet zc5 la den lyse kanten under vannlinjestripen paa akterspeilet i
z = 0 (DWL). Da havner fenderlisten paa akterspeilet ca. 116 mm under listen
paa siden. IMG_9370 (baaten flyter, kvadratiske piksler, kamera stilt inn
etter fenderlisten og stevnen) viser at vannet ligger paa modellens DWL
(+-2 cm) og overgangen til roedt ca. 38 mm over.

Her loeses kameraet med andre hoeydeankre:
  stripe38: stripens nedre kant z = 38 +- 10 (som paa siden), listen fri
  liste:    fenderlisten som i modellen (hjoerner 804, bue 42 opp midt paa), stripen fri
  begge:    begge ankrene
og bunnen av roret (spissen i u 705, v 1575) regnes ut som kontroll
(Enderlein: ca. -1 047 under DWL).

Kjoeres fra denne mappa: python cam9391e.py
"""
import json

import numpy as np
from scipy.optimize import least_squares

import common as c, uwlib as U
import cam9391 as K

Y = 560.0
ys = np.linspace(-Y, Y, 113)


def strake3(zc, a):
    z = zc - a * (ys / Y) ** 2
    return np.c_[[U.transom_x(zz, y) + 13.0 for zz, y in zip(z, ys)], ys, z]


ST_ALL = np.array(json.load(open(c.W + "/out/t9391.json"))["strake"])
ST = np.c_[ST_ALL[:, 0], 0.5 * (ST_ALL[:, 1] + ST_ALL[:, 2])]


def res(q, mode, parts=False):
    # q: 7 kamera, zt (stripens overkant), zcr (nedre kant), zs (listens hjoerner), a (bue)
    K.st_c = ST
    K.STRAKE3 = strake3(q[9] + q[10], q[10])
    p9 = list(q[:9])
    g = K.residuals(p9, True)
    pri = [(q[6] - 1495.0) / (8.0 if mode.endswith("f") else 40.0)]
    if mode in ("stripe38", "begge", "stripe38f"):
        pri.append((q[8] - 38.0) / 10.0)
    else:
        pri.append((q[8] - 38.0) / 300.0)
    if mode in ("liste", "begge"):
        pri += [(q[9] - 804.0) / 10.0, (q[10] - 42.0) / 10.0]
    else:
        pri += [(q[9] - 804.0) / 1000.0, (q[10] - 42.0) / 30.0]
    g["prior"] = np.array(pri) * 3.0
    if parts:
        return g
    return np.concatenate([v / np.sqrt(max(len(v), 1) / 30.0) if k != "prior" else v for k, v in g.items()])


def rudder_bottom(p):
    cam = U.Cam(p[:7], 1500, 2000)
    d = np.array([(705 - cam.cx) / cam.f, (1575 - cam.cy) / cam.f, 1.0]) @ cam.R
    return {X: float((cam.C + (X - cam.C[0]) / d[0] * d)[2]) for X in (8150.0, 8250.0)}


if __name__ == "__main__":
    z5 = json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"]
    import sys
    modes = sys.argv[1:] or ["stripe38", "liste", "begge", "stripe38f"]
    try:
        out = json.load(open(c.W + "/out/cam9391e.json"))
    except OSError:
        out = {}
    for mode in modes:
        best = None
        for dz in (0.0, -60.0, -120.0):
            s = list(z5[:7]) + [z5[7] + 40.0, 38.0, 804.0, 42.0]
            s[2] += dz
            r = least_squares(lambda q: res(q, mode), s,
                              bounds=([8300, -1500, -1600, 160, -20, -15, 1100, -100, -150, 500, -100],
                                      [14000, 1500, 1500, 190, 30, 15, 2200, 500, 300, 1100, 300]),
                              x_scale=[200, 50, 100, 1, 1, 1, 50, 20, 10, 20, 10],
                              loss="soft_l1", f_scale=4.0, max_nfev=600)
            if best is None or r.cost < best.cost:
                best = r
        g = res(best.x, mode, True)
        rms = {k: round(float(np.sqrt(np.mean(np.square(v)))), 2) for k, v in g.items()}
        rb = rudder_bottom(best.x)
        print(f"{mode:9s} kamera z {best.x[2]:7.1f} x {best.x[0]:7.1f} pitch {best.x[4]:5.2f} f {best.x[6]:6.1f} | "
              f"stripe {best.x[8]:5.1f}..{best.x[7]:5.1f} | liste hjoerner {best.x[9]:5.1f} bue {best.x[10]:4.1f} | "
              f"rorbunn {rb[8150.0]:.0f}/{rb[8250.0]:.0f} | rms {rms}", flush=True)
        out[mode] = dict(p=best.x, rms=rms, rudder_bottom=rb)
    rb = rudder_bottom(z5)
    print(f"zc5 (foer)  kamera z {z5[2]:.1f} | stripe {z5[8]:.1f}..{z5[7]:.1f} | liste {z5[9]:.1f} | rorbunn {rb[8150.0]:.0f}/{rb[8250.0]:.0f}")
    c.save_json(out, c.W + "/out/cam9391e.json")
