"""Skeptikerens kontroll av cockpit-spesifikasjonen (ck_spec.json), 13.11.2026.

Andre metoder enn maaleren:
 1. nye (5) (eierens baat): brennvidden f fra teakgitterets rutenett
    (kvadratiske ruter -> forkortningen sin(delta) gir siktvinkelen mot
    planet), deretter brodekkets dybde fra tre rader i samme kolonne
    (ruffens fot, brodekkets akterkant, bronnveggens fot paa gitteret) og
    bronnveggens hoeyde (sete - gitter). Bare tall, ingen bilder skrives
    (bildet viser folk).
 2. Brosjyrefotoet (s. 7): kryssforhold langs senterlinjen med
    forsvinningspunktet fra lokkenes og fotbroennens langsgaaende kanter.
 3. 448-5: den stiplede linjen ved z 815-830 mot modellens fenderliste
    (er tegningen 30 mm hoeyere enn modellen?).

    python tools/memcap.py --gb 3 -- python v10/verktoy/foto/py/chk_ck_verify.py

Uten CadQuery (bare hr26.params og hr26.curves).
"""
from __future__ import annotations

import io
import itertools
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import maximum_filter, uniform_filter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
from hr26 import curves as C  # noqa: E402

HOME = os.path.join(os.path.expanduser("~"), "Documents", "Seilbåt")
SRC = os.path.join(HOME, "Hallberg-Rassy-kilder")
OUT = os.path.join(ROOT, "v10", "rapporter", "13nov_nye", "chk_ck_resultat.json")
R = {}

# ------------------------------------------------------------- 1. nye (5)
N5 = np.asarray(Image.open(os.path.join(HOME, "nye_2026-11-13", "nye (5).jpeg")).convert("L"), float)
CX, CY = 585.0, 788.0          # bildet er hele 3:4-rammen (1170 x 1556 + svarte kanter)
VH = 693.0                     # strandlinjen (land/vann) venstre 694-699, hoeyre 683-706


def lattice(x0, x1, y0, y1):
    """De to korteste gittervektorene (px) fra autokorrelasjonen."""
    p = N5[y0:y1, x0:x1].copy()
    p = p - uniform_filter(p, 15)
    p *= np.hanning(p.shape[0])[:, None] * np.hanning(p.shape[1])[None, :]
    f = np.fft.fft2(p)
    a = np.fft.fftshift(np.real(np.fft.ifft2(f * np.conj(f))))
    cy, cx = np.array(a.shape) // 2
    a /= a[cy, cx]
    ys, xs = np.nonzero((a == maximum_filter(a, 5)) & (a > 0.15))
    pk = sorted((math.hypot(x - cx, y - cy), x - cx, y - cy) for x, y in zip(xs, ys) if (x, y) != (cx, cy))
    v1 = np.array(pk[0][1:])
    v2 = next(np.array(q[1:]) for q in pk if abs(float(v1[0] * q[2] - v1[1] * q[1])) > 0.5 * q[0] * pk[0][0])
    return v1, v2


def depression(f, u, v):
    th = math.atan((CY - VH) / f)
    r = np.array([u - CX, v - CY, f])
    return math.degrees(math.asin((r[1] * math.cos(th) + r[2] * math.sin(th)) / np.linalg.norm(r)))


grid = []
for box in ((615, 790, 1370, 1445), (600, 720, 1455, 1525)):
    a, b = lattice(*box)
    s = np.linalg.svd(np.column_stack([a, b]), compute_uv=False)
    meas = math.degrees(math.asin(s[1] / s[0]))
    uc, vc = 0.5 * (box[0] + box[1]), 0.5 * (box[2] + box[3])
    pred = {f: round(depression(f, uc, vc), 1) for f in (540, 579, 650, 900, 1172)}
    grid.append({"box": box, "a": a.tolist(), "b": b.tolist(), "ratio": round(s[1] / s[0], 3),
                 "delta_meas_deg": round(meas, 1), "delta_pred_deg": pred})
R["n5_gitter"] = grid


def bridge_depth(f, vh, cy, va, vf, vs, h):
    th = math.atan((cy - vh) / f)

    def t(v):
        return math.tan(th + math.atan((v - cy) / f))
    da = h / (t(vs) - t(va))
    hc = da * t(va)
    return hc / t(vf) - da, da, hc


# kolonne x 805 (hoeyre for nedgangen): ruffens fot 1042, akterkant (nesen) 1125,
# veggens fot paa gitteret 1325 (kolonneprofiler); veggen 395-425 hoey
res = {}
for f in (540, 579, 620, 650, 900, 1172):
    d, da, hc = [], [], []
    for vh, cy, va, vf, vs, h in itertools.product((685, 693, 700), (770, 788, 806), (1119, 1125, 1131),
                                                   (1037, 1042, 1047), (1320, 1325, 1330), (395, 425)):
        q = bridge_depth(f, vh, cy, va, vf, vs, h)
        d.append(q[0]); da.append(q[1]); hc.append(q[2])
    res[f] = {"D_median": round(float(np.median(d))), "D_p10": round(float(np.percentile(d, 10))),
              "D_p90": round(float(np.percentile(d, 90))), "kamera_til_akterkant": round(float(np.median(da))),
              "kamera_over_brodekk": round(float(np.median(hc)))}
R["n5_brodekk"] = res

# ------------------------------------------------- 2. brosjyrefotoet s. 7
import pymupdf  # noqa: E402
doc = pymupdf.open(os.path.join(SRC, "HR26brochure.pdf"))
pg = doc[6]
rc = pg.rect
clip = pymupdf.Rect(rc.width * 40 / 910, rc.height * 845 / 1286, rc.width * 305 / 910, rc.height * 1120 / 1286)
BR = np.asarray(Image.open(io.BytesIO(pg.get_pixmap(dpi=300, clip=clip).tobytes("png"))).convert("L"), float)


def row_edges(y, thr=70):
    row = BR[y - 1:y + 2, :].mean(axis=0)
    out, last = [], -10
    for i in range(1, len(row) - 3):
        if abs(row[i + 2] - row[i]) > thr and i - last > 4:
            out.append((i + 1, "D" if row[i + 2] < row[i] else "U"))
            last = i
    return out


def fit_line(pts):
    y = np.array([p[1] for p in pts], float)
    x = np.array([p[0] for p in pts], float)
    k, m = np.polyfit(y, x, 1)
    return k, m


# lokkenes ytterkanter (lest av row_edges ved y 360-580; se rapporten)
L_out = [(166, 360), (162, 380), (156, 420), (150, 460), (136, 540), (134, 570), (132, 580)]
R_out = [(552, 360), (556, 380), (564, 420), (572, 460), (578, 500), (586, 540), (590, 570)]
k1, m1 = fit_line(L_out)
k2, m2 = fit_line(R_out)
V = (m2 - m1) / (k1 - k2)
vA, vB, vC = 263.0, 603.0, 684.0   # aktre bronnvegg topp, brodekkets akterkant (skinna), nedgangens kant


def xr(v, vv):
    return 1.0 / (v - vv)


cr = {}
for vv in (V, -590.0, -1200.0, -1e9):
    r = (xr(vB, vv) - xr(vC, vv)) / (xr(vA, vv) - xr(vB, vv))
    lid_f = (xr(vB, vv) - xr(581.0, vv)) / (xr(vA, vv) - xr(vB, vv))
    lid_a = (xr(vB, vv) - xr(353.0, vv)) / (xr(vA, vv) - xr(vB, vv))
    wall = (xr(vA, vv) - xr(321.0, vv)) / (xr(vA, vv) - xr(vB, vv))
    cr[str(round(vv))] = {"synlig_brodekk_per_L": round(r, 3), "lokk_forkant": round(-lid_f, 3),
                          "lokk_akterkant": round(-lid_a, 3), "veggfot_skift_per_L": round(wall, 3)}
R["brosjyrefoto"] = {"V_x_rad": round(V, 0), "rader": {"A": vA, "B": vB, "C": vC}, "kryssforhold": cr,
                     "sjekk_lokk_brosjyreplan": {"forkant": round((6130 - 6067) / 1221, 3),
                                                  "akterkant": round((6912 - 6067) / 1221, 3)}}
# modellramme: bronnfront 5660 og aktre vegg 7300 faste -> xB = (5660 + r*7300 + skjult)/(1 + r)
R["brosjyrefoto"]["xB_modell"] = {f"r{r}_skjult{h}": round((5660 + r * 7300 + h) / (1 + r))
                                  for r in (0.16, 0.18, 0.21, 0.24) for h in (20, 60, 100)}

# --------------------------------------------- 3. 448-5 mot modellens liste
E = np.asarray(Image.open(os.path.join(SRC, "HR26interior448-5.jpeg")).convert("L"), float)
ES, EU0, EV0 = 4.2591, 2240.1, 541.8


def runs(m):
    out, i = [], 0
    while i < len(m):
        if m[i]:
            j = i
            while j < len(m) and m[j]:
                j += 1
            out.append((i, j - 1))
            i = j
        else:
            i += 1
    return out


tab = []
for x in (3000, 4000, 5000, 6200, 6600, 7000, 7400):
    u = int(round(EU0 - x / ES))
    col = E[300:400, u - 2:u + 3].min(axis=1)
    zs = [round((EV0 - (300 + 0.5 * (a + b))) * ES) for a, b in runs(col < 165)]
    zs = [z for z in zs if 780 < z < 940]
    zm = round(C.strake_z(x))
    near = min(zs, key=lambda z: abs(z - zm)) if zs else None
    tab.append({"x": x, "448_5_linjer_780_940": zs, "modell_liste": zm,
                "diff": None if near is None else near - zm})
R["e448_5_liste"] = tab
json.dump(R, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(R, indent=1, ensure_ascii=False))
