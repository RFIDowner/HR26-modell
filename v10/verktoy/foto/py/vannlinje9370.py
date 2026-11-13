"""Vannlinjestripen og vannflaten langs baaten paa IMG_9370 (baaten flyter,
fra siden), i modellens hoeyder (13.11.2026 kveld).

Kameraet er det ortografiske fra stevn9370.py (out/stevn9370.json), stilt
inn etter fenderlisten, stevnhodet og akterspeilets linje - ikke etter
stripen eller vannet. Stripens overkant, overgangen til roedt og vannkanten
(v10/arbeid/v10/photo/m9370_bt.json) tilbakeprojiseres til skrogsiden:
punktet (x, y, z) med y = spantets halvbredde i hoeyden z.

Svarer paa: hvor ligger stripen og vannet i modellens hoeyder, forut og
akter? Det avgjoer hvilken hoeyde stripen paa akterspeilet har i IMG_9391.

Kjoeres fra denne mappa: python vannlinje9370.py
"""
import json
import math

import numpy as np

import common as c

C = c.C
import sys
from scipy.optimize import least_squares
import stevn9370 as S9

SQUARE = "ikke-kvadrat" not in sys.argv


def fit_square():
    """Som stevn9370.fit, men med kvadratiske piksler (su = sv)."""
    best = None
    for th0 in (-5, 0, 5):
        for ph0 in (0, 5, 10):
            f6 = lambda q: S9.resid(np.r_[q[0], q[1], q[1], q[2:]])
            s = least_squares(f6, [-1.8, 9.6, 160, 1352, th0, ph0], x_scale=[1, .5, 5, 5, 2, 2],
                              bounds=([-10, 5, 0, 1200, -40, -20], [10, 15, 400, 1500, 40, 30]))
            if best is None or s.cost < best.cost:
                best = s
    q = best.x
    return np.r_[q[0], q[1], q[1], q[2:]]


cam = fit_square() if SQUARE else json.load(open(c.W + "/out/stevn9370.json"))["cam"]
rho, su, sv, u0, v0, th, ph = cam
for nm, obs, mod in (("akterspeil", S9.tr, S9.tr_m), ("fenderlist", S9.S, S9.strake_m), ("stevnhode", S9.head_px[None], S9.head)):
    r = S9.cres(obs, S9.proj(np.asarray(cam), mod))
    print("kamera %s: rho %.2f su %.3f sv %.3f yaw %.2f elev %.2f | %s rms %.2f px"
          % ("kvadrat" if SQUARE else "fritt", rho, su, sv, th, ph, nm, np.sqrt((r ** 2).mean())))
t, f = math.radians(th), math.radians(ph)
cr, sr = math.cos(math.radians(rho)), math.sin(math.radians(rho))
d = json.load(open(c.REPO + "/v10/arbeid/v10/photo/m9370_bt.json"))
bt = np.array(d["bt"], float)        # u, overkant blaa, start roedt
red = np.array(d["red"], float)      # u, siste roede rad + 0,5 (vannkanten), foerste roede rad


def half_width(x, z):
    p = C._section_geom(round(float(x), 0))["pts"]
    zz = np.maximum.accumulate(p[:, 1])
    if z <= zz[0]:
        return 0.0
    return float(np.interp(z, zz, p[:, 0]))


def back(u, v):
    a = cr * (u - u0) + sr * (v - v0)
    b = -sr * (u - u0) + cr * (v - v0)
    y, x, z = 900.0, 4000.0, 0.0
    for _ in range(6):
        x = (a * su - y * math.sin(t)) / math.cos(t)
        z = (-b * sv + (-x * math.sin(t) + y * math.cos(t)) * math.sin(f)) / math.cos(f)
        if not (0.0 < x < 7950.0):
            return None
        y = half_width(x, z)
    return x, y, z


def line(arr, col):
    out = []
    for r in arr:
        if np.isfinite(r[col]):
            q = back(r[0], r[col])
            if q is not None:
                out.append(q)
    return np.array(out)


top = line(bt, 1)
cream = line(bt, 2)
water = line(red, 1)
bins = np.arange(1000.0, 8000.0, 500.0)
print("x-omraade        stripe overkant   overgang roedt   vannkant    (z over modellens DWL, mm)")
res = []
for x0 in bins:
    row = [x0]
    for L in (top, cream, water):
        m = (L[:, 0] >= x0) & (L[:, 0] < x0 + 500.0) if len(L) else np.array([], bool)
        row.append(float(np.median(L[m, 2])) if m.sum() >= 3 else np.nan)
    res.append(row)
    print(f"  {x0:5.0f}-{x0 + 500:5.0f}     {row[1]:7.0f}          {row[2]:7.0f}        {row[3]:7.0f}")
for name, L in (("overkant", top), ("roedt", cream), ("vann", water)):
    if len(L) > 10:
        k = np.polyfit(L[:, 0], L[:, 2], 1)
        print(f"rett linje {name}: z = {k[1]:.0f} + {k[0] * 1000:.1f} mm per m  (x {L[:, 0].min():.0f}-{L[:, 0].max():.0f})"
              f"  -> ved akterspeilet (7806): {np.polyval(k, 7806):.0f}")
c.save_json(dict(top=top, cream=cream, water=water, bins=res), c.W + "/out/vannlinje9370%s.json" % ("" if SQUARE else "_fritt"))
