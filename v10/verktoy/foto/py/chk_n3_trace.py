"""Skeptikerens egne spor i «nye (3).jpeg» (13.11.2026, kontroll av
akter-maaleren). Uavhengig av n3_trace.py: sporene tas langs normalen til en
haandlest grovkurve (ikke per rad/kolonne), og alt lagres i
../out/chk_n3_trace.json.

BILDET VISER FOLK: ingenting fra bildet skrives i repoet (bare tall).

  knuckle   styrbord akterspeilhjoerne, sterkeste lys/skygge-kant langs
            normalen til grovkurven, fra like under listen ned til stripen
  strake    fenderlistens senter (moerkt baand, tilpasset filter) per kolonne
  bt        vannlinjestripens blaa overkant per kolonne (hvit -> blaa)
  keel_*    kjolens kanter og bunn (roedt mot asfalt)
  rudder    rorets nederste punkt og stripen paa roret

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python chk_n3_trace.py
"""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.interpolate import splprep, splev

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/nye (3).jpeg"
A = np.asarray(Image.open(SRC).convert("RGB")).astype(float)
H_, W_ = A.shape[:2]
R, G, B = A[..., 0], A[..., 1], A[..., 2]
L = A.mean(2)
L2 = ndi.gaussian_filter(L, 2.0)
out = {"W": W_, "H": H_}


def bilin(img, x, y):
    return ndi.map_coordinates(img, [np.atleast_1d(y), np.atleast_1d(x)], order=1)


def trace_normal(img, seed, half=14, step=6.0, sign=0, iters=2):
    """Sterkeste kant langs normalen til en glatt kurve gjennom seed (u, v)."""
    s = np.asarray(seed, float)
    for _ in range(iters):
        tck, _u = splprep([s[:, 0], s[:, 1]], s=len(s) * 4.0, k=3)
        L_ = np.sum(np.hypot(*np.diff(np.array(splev(np.linspace(0, 1, 400), tck)), axis=1)))
        ts = np.linspace(0, 1, int(L_ / step) + 1)
        px, py = splev(ts, tck)
        dx, dy = splev(ts, tck, der=1)
        n = np.hypot(dx, dy)
        nx, ny = -dy / n, dx / n
        off = np.arange(-half, half + 0.01, 0.5)
        pts = []
        for x0, y0, a, b in zip(px, py, nx, ny):
            prof = bilin(img, x0 + off * a, y0 + off * b)
            g = np.gradient(prof)
            if sign:
                g = g * sign
                k = int(np.argmax(g))
            else:
                k = int(np.argmax(np.abs(g)))
            if 1 <= k < len(g) - 1:
                pts.append([x0 + off[k] * a, y0 + off[k] * b, float(g[k])])
        s = np.array(pts)
    return s


# ---- styrbord akterspeilhjoerne -----------------------------------------------------
SEED_K = [(781, 1090), (776, 1145), (765, 1180), (755, 1210), (740, 1235), (722, 1258), (700, 1275),
          (670, 1293), (640, 1306), (615, 1316), (597, 1322)]
for sgn in (+1, -1):
    k = trace_normal(L2, SEED_K, half=12, step=4.0, sign=sgn)
    out["knuckle_s%+d" % sgn] = k.tolist()
k = trace_normal(L2, SEED_K, half=12, step=4.0, sign=0)
out["knuckle"] = k.tolist()

# ---- fenderlisten: moerkt baand, tilpasset filter (12 px hoeyt) -------------------
SEED_S = [(25, 1058), (100, 1046), (200, 1031), (300, 1019), (450, 1012), (550, 1013), (650, 1024),
          (750, 1042), (800, 1053), (850, 1068), (900, 1086), (950, 1101), (985, 1112)]
gS = np.array(SEED_S, float)
strake = []
box = ndi.uniform_filter1d(L2, 11, axis=0)
for u in range(28, 988, 3):
    if 360 <= u <= 455 or 640 <= u <= 676:        # rorhodet og kjettingen
        continue
    vg = np.interp(u, gS[:, 0], gS[:, 1])
    lo, hi = int(vg - 20), int(vg + 20)
    prof = box[lo:hi, u]
    k = int(np.argmin(prof))
    if 1 <= k < len(prof) - 1:
        a, b_, c_ = prof[k - 1], prof[k], prof[k + 1]
        den = a - 2 * b_ + c_
        kk = k + (0.5 * (a - c_) / den if abs(den) > 1e-9 else 0.0)
        contrast = float(np.percentile(L2[lo:hi, u], 90) - prof[k])
        if contrast > 40:
            strake.append([u, lo + kk, contrast])
out["strake"] = strake

# ---- vannlinjestripens blaa overkant ---------------------------------------------------
bt = []
for u in range(150, 985, 3):
    if 368 <= u <= 452 or 645 <= u <= 672:
        continue
    prof = L2[1280:1400, u]
    blue = (B[1280:1400, u] > R[1280:1400, u] + 5)
    g = np.gradient(prof)
    k = int(np.argmin(g))
    if g[k] < -6:
        a, b_, c_ = g[k - 1], g[k], g[k + 1]
        den = a - 2 * b_ + c_
        bt.append([u, 1280 + k + (0.5 * (a - c_) / den if abs(den) > 1e-9 else 0.0), float(g[k])])
out["bt"] = bt

# ---- kjolen ---------------------------------------------------------------------------
KR = (R - G > 10) & (R - B > 8)
KR = ndi.binary_opening(KR, iterations=1)
kl, kr = [], []
for v in range(1520, 1735, 3):
    idx = np.where(KR[v, 560:700])[0]
    if len(idx) < 20:
        continue
    runs = np.split(idx, np.where(np.diff(idx) > 2)[0] + 1)
    run = max(runs, key=len)
    a, b_ = 560 + run[0], 560 + run[-1]
    pa = L2[v, a - 6:a + 6]; pb = L2[v, b_ - 6:b_ + 6]
    ga = np.gradient(pa); gb = np.gradient(pb)
    kl.append([a - 6 + int(np.argmax(np.abs(ga))), v]); kr.append([b_ - 6 + int(np.argmax(np.abs(gb))), v])
out["keel_l"], out["keel_r"] = kl, kr
kb = []
for u in range(580, 660, 2):
    idx = np.where(KR[1650:1800, u])[0]
    if len(idx) < 5:
        continue
    runs = np.split(idx, np.where(np.diff(idx) > 2)[0] + 1)
    run = max(runs, key=len)
    kb.append([u, 1650 + run[-1] + 0.5])
out["keel_bot"] = kb

# ---- roret: nederste punkt og stripen paa roret ----------------------------------------
RR = (R - G > 30) & (R - B > 25)
RR = ndi.binary_opening(RR, iterations=1)
tips = []
for u in range(440, 500):
    idx = np.where(RR[1780:1900, u])[0]
    if len(idx):
        tips.append([u, 1780 + idx.max() + 0.5])
tips = np.array(tips)
out["rudder_tip"] = tips[np.argmax(tips[:, 1])].tolist()
out["rudder_bottom_cols"] = tips.tolist()
# stripen paa roret (blaa overkant, hvit linje -> roedt) i kolonnene u 395-430
rs = []
for u in range(392, 432, 2):
    prof = L2[1320:1400, u]
    g = np.gradient(prof)
    k1 = int(np.argmin(g))                       # hvit -> blaa
    rcol = (R[1320:1400, u] - G[1320:1400, u])
    kr_ = int(np.argmax(np.gradient(ndi.gaussian_filter1d(rcol, 1.5))))   # -> roedt
    rs.append([u, 1320 + k1, 1320 + kr_])
out["rudder_stripe"] = rs

with open(os.path.join(HERE, "..", "out", "chk_n3_trace.json"), "w") as fh:
    json.dump(out, fh, indent=1, default=float)
for k_, v_ in out.items():
    if isinstance(v_, list):
        print(f"{k_:16s} {len(v_):4d}")
print("rorets nederste punkt", out["rudder_tip"])
kn = np.array(out["knuckle"])
print("knuckle (u, v) hver 4.:", np.round(kn[::4, :2]).astype(int).tolist())
print("rudder stripe", rs[::4])
