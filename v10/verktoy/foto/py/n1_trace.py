"""Spor i «nye (1).jpeg» (1170 x 2532, skjermklipp; baaten i stroppene, sett
akterfra og nedenfra). 13.11.2026, akter-maaleren.

Hvert trekk har en guide (lest av paa forstoerrede utsnitt) og forfines
lokalt i bildet:
  strake_port    fenderlisten paa babord side (moerk gummi mot himmel/hvit),
                 senter av det moerke baandet per rad, v 640-1080
  strake_port_tr listen tvers over akterspeilet, babord del (u 226-350)
  strake_stbd    listen ved styrbord hjoerne og ned langs siden
  top            akterspeilets overkant (hvit mot himmel), u 300-635 og 715-910
  rudder         rorets lyse (roede) kant, v 880-1530 (svak: roret er vridd)
  keel_l/r/bot   kjolens omriss mot himmel/traer (fiolett-roed mot blaatt/groent)
  knuckle        akterspeilhjoernet paa babord side over stripen (lys/skygge-
                 grense, sporet i et hoeypassfiltrert bilde)
  bt_top, cream  vannlinjestripens blaa overkant og den lyse linja under den
                 (overgangen til roedt) - knekkene er hjoernet i de hoeydene
  sil_l, sil_r   skrogets omriss mot himmel (til spoersmaal 2)

Kjoeres fra denne mappa:  python ../../../../tools/memcap.py --gb 3 -- python n1_trace.py [sjekk.png]
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

import common as c

SRC = r"C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/nye (1).jpeg"
A = np.asarray(Image.open(SRC).convert("RGB")).astype(float)
H_, W_ = A.shape[:2]
R, G, B = A[..., 0], A[..., 1], A[..., 2]
L = A.mean(2)
Ls = ndi.gaussian_filter(L, 1.2)
SKY = (B > R + 35) & (B > 120)


def gi(guide, t):
    g = np.asarray(guide, float)
    return float(np.interp(t, g[:, 0], g[:, 1]))


def dark_center_row(v, ug, half=18, thr_frac=0.5):
    lo, hi = int(ug - half), int(ug + half)
    prof = Ls[v, lo:hi]
    mn, bg = prof.min(), np.percentile(prof, 85)
    thr = mn + thr_frac * (bg - mn)
    k = int(np.argmin(prof))
    a = k
    while a > 0 and prof[a - 1] < thr:
        a -= 1
    b = k
    while b < len(prof) - 1 and prof[b + 1] < thr:
        b += 1
    if bg - mn < 60 or a == 0 or b == len(prof) - 1:
        return None
    return lo + 0.5 * (a + b), b - a + 1


def dark_center_col(u, vg, half=12, thr_frac=0.5):
    lo, hi = int(vg - half), int(vg + half)
    prof = Ls[lo:hi, u]
    mn, bg = prof.min(), np.percentile(prof, 85)
    thr = mn + thr_frac * (bg - mn)
    k = int(np.argmin(prof))
    a = k
    while a > 0 and prof[a - 1] < thr:
        a -= 1
    b = k
    while b < len(prof) - 1 and prof[b + 1] < thr:
        b += 1
    if bg - mn < 60 or a == 0 or b == len(prof) - 1:
        return None
    return lo + 0.5 * (a + b), b - a + 1


def edge_sub(prof):
    """Sterkeste kant (subpiksel) i en profil: indeks."""
    g = np.gradient(prof)
    k = int(np.argmax(np.abs(g)))
    if 0 < k < len(g) - 1:
        a, b, cc = abs(g[k - 1]), abs(g[k]), abs(g[k + 1])
        den = a - 2 * b + cc
        return k + (0.5 * (a - cc) / den if abs(den) > 1e-9 else 0.0), float(g[k])
    return float(k), float(g[k])


out = {"W": W_, "H": H_}

# ---- fenderlisten, babord side ------------------------------------------------
g1 = [(632, 200), (668, 180), (700, 173), (800, 142), (900, 109), (1000, 77), (1085, 55)]
pts = []
for v in range(642, 1084, 4):
    r = dark_center_row(v, gi(g1, v), 16)
    if r and 8 <= r[1] <= 30:
        pts.append([r[0], v, r[1]])
out["strake_port"] = pts

# ---- listen tvers over akterspeilet (babord del) -----------------------------
# stigen (staalroer) krysser ved u 266-332; bare u 214-262 og 336-352 brukes
g2 = [(214, 634), (260, 629), (340, 617), (352, 615)]
pts = []
for u in list(range(214, 263, 3)) + list(range(336, 353, 3)):
    r = dark_center_col(u, gi(g2, u), 16)
    if r and 10 <= r[1] <= 32:
        pts.append([u, r[0], r[1]])
out["strake_port_tr"] = pts

# ---- listen ved styrbord hjoerne ----------------------------------------------
# siden: bare den indre (venstre) kanten hvit -> moerk; utenfor er gaffeltrucken moerk
g3 = [(762, 1099), (800, 1099), (830, 1098), (860, 1095)]
pts = []
for v in range(762, 862, 4):
    ug = gi(g3, v)
    lo = int(ug - 10)
    e, gk = edge_sub(Ls[v, lo:lo + 20])
    if gk < -15:
        pts.append([lo + e, v, gk])
out["strake_stbd_in"] = pts
g3b = [(1066, 731), (1076, 733), (1088, 740)]
pts = []
for u in range(1066, 1089, 2):
    r = dark_center_col(u, gi(g3b, u), 16)
    if r and 10 <= r[1] <= 34:
        pts.append([u, r[0], r[1]])
out["strake_stbd_tr"] = pts

# babord side: ogsaa den indre (hoeyre) kanten moerk -> hvit
pts = []
for p in out["strake_port"]:
    v = int(p[1]); lo = int(p[0])
    e, gk = edge_sub(Ls[v, lo:lo + 22])
    if gk > 15:
        pts.append([lo + e, v, gk])
out["strake_port_in"] = pts

# ---- akterspeilets overkant (hvit mot himmel) --------------------------------
g4 = [(300, 537), (450, 538), (635, 545), (715, 569), (821, 594), (910, 612)]
pts = []
for u in list(range(300, 636, 5)) + list(range(716, 911, 5)):
    vg = gi(g4, u)
    lo, hi = int(vg - 14), int(vg + 14)
    col = SKY[lo:hi, u]
    wht = (L[lo:hi, u] > 170) & ~col
    # siste himmelpiksel over foerste hvite i en sammenhengende hvit stripe
    idx = np.where(wht)[0]
    if len(idx) == 0 or not col[:max(idx[0], 1)].any():
        continue
    k = idx[0]
    prof = Ls[lo:hi, u]
    e, gk = edge_sub(prof[max(k - 4, 0):k + 4])
    vv = lo + max(k - 4, 0) + e
    pts.append([u, vv])
out["top"] = pts

# ---- roret: den lyse kanten ----------------------------------------------------
pts = []
for v in range(880, 1532, 6):
    lo, hi = 664, 696
    prof = ndi.gaussian_filter1d(R[v, lo:hi], 1.0)
    k = int(np.argmax(prof))
    if 0 < k < len(prof) - 1:
        a, b, cc = prof[k - 1], prof[k], prof[k + 1]
        den = a - 2 * b + cc
        k = k + (0.5 * (a - cc) / den if abs(den) > 1e-9 else 0.0)
    pts.append([lo + k, v])
out["rudder"] = pts

# ---- kjolen ---------------------------------------------------------------------
KEEL = (R - G > 6) & (B - G > 6) & (L < 140)
KEEL = ndi.binary_opening(KEEL, iterations=1)
kl, kr, kb = [], [], []
for v in range(1872, 2052, 4):
    row = KEEL[v, 420:620]
    idx = np.where(row)[0]
    if len(idx) < 10:
        continue
    # lengste sammenhengende kjolstykke
    runs = np.split(idx, np.where(np.diff(idx) > 2)[0] + 1)
    run = max(runs, key=len)
    a, b = 420 + run[0], 420 + run[-1]
    ea, _ = edge_sub(Ls[v, a - 5:a + 5]); eb, _ = edge_sub(Ls[v, b - 5:b + 5])
    kl.append([v, a - 5 + ea])
    if v <= 1995:
        kr.append([v, b - 5 + eb])
# bunnen: nedenfra (traer/hus bak) opp til foerste sammenhengende kjolpiksler
KB = (R >= G - 2) & (B >= G - 4) & (L < 115)
for u in range(474, 552, 3):
    col = KB[1990:2100, u]
    b = None
    for k in range(len(col) - 1, 4, -1):
        if col[k - 4:k + 1].all():
            b = 1990 + k
            break
    if b is None:
        continue
    e, _ = edge_sub(Ls[b - 5:b + 6, u])
    kb.append([u, b - 5 + e])
out["keel_l"], out["keel_r"], out["keel_bot"] = kl, kr, kb

# ---- akterspeilhjoernet over stripen (babord) ----------------------------------
HP = ndi.gaussian_filter(L, 2.0) - ndi.gaussian_filter(L, 25.0)
HPs = ndi.gaussian_filter(HP, 1.5)
gk_rows = [(690, 203), (725, 210), (760, 215), (800, 225), (830, 240), (860, 265)]
gk_cols = [(270, 864), (300, 885), (325, 900), (350, 910), (380, 920), (410, 932), (435, 945), (455, 955)]
kn = []
for v in range(700, 862, 4):
    ug = gi(gk_rows, v)
    lo = int(ug - 12)
    prof = HPs[v, lo:lo + 24]
    e, gval = edge_sub(prof)
    kn.append([lo + e, v, gval])
for u in range(272, 456, 4):
    vg = gi(gk_cols, u)
    lo = int(vg - 10)
    prof = HPs[lo:lo + 20, u]
    e, gval = edge_sub(prof)
    kn.append([u, lo + e, gval])
out["knuckle"] = kn

# ---- vannlinjestripen: blaa overkant og den lyse linja under ------------------
BLUE = (B > R + 18) & (B > G + 8) & (L < 120)
bt, cr = [], []
for u in range(250, 1060, 3):
    col = BLUE[850:1450, u]
    idx = np.where(col)[0]
    if len(idx) < 8:
        continue
    runs = np.split(idx, np.where(np.diff(idx) > 3)[0] + 1)
    run = max(runs, key=len)
    if len(run) < 10:
        continue
    a, b = 850 + run[0], 850 + run[-1]
    ea, _ = edge_sub(Ls[a - 5:a + 5, u])
    top = a - 5 + ea
    # den lyse linja: lysmaksimum like under den blaa
    prof = ndi.gaussian_filter1d(L[b - 3:b + 14, u], 0.8)
    k = int(np.argmax(prof))
    if 0 < k < len(prof) - 1:
        p0, p1, p2 = prof[k - 1], prof[k], prof[k + 1]
        den = p0 - 2 * p1 + p2
        k = k + (0.5 * (p0 - p2) / den if abs(den) > 1e-9 else 0.0)
    bt.append([u, top])
    cr.append([u, b - 3 + k, float(prof.max())])
out["bt_top"], out["cream"] = bt, cr

# ---- skrogets omriss mot himmel (spoersmaal 2) ----------------------------------
DARK = A.max(2) < 70
sl, sr = [], []
for v in range(1100, 1860, 5):
    row = SKY[v]
    # fra venstre: foerste piksel som ikke er himmel og ikke del av staven/stroppen
    nz = np.where(~row[:700])[0]
    if len(nz):
        a = int(nz[0])
        e, _ = edge_sub(Ls[v, max(a - 5, 0):a + 5])
        sl.append([max(a - 5, 0) + e, v, bool(DARK[v, a:a + 6].mean() > 0.5)])
    nz = np.where(~row[560:])[0]
    if len(nz):
        b = 560 + int(nz[-1])
        e, _ = edge_sub(Ls[v, b - 5:b + 5])
        sr.append([b - 5 + e, v, bool(DARK[v, b - 6:b + 1].mean() > 0.5)])
out["sil_l"], out["sil_r"] = sl, sr

c.save_json(out, c.W + "/out/n1_trace.json")
for k, v in out.items():
    if isinstance(v, list):
        print(f"{k:15s} {len(v):4d}")

if len(sys.argv) > 1:
    from PIL import ImageDraw
    im = Image.open(SRC).convert("RGB")
    d = ImageDraw.Draw(im)
    col = dict(strake_port=(255, 255, 0), strake_port_tr=(255, 255, 0), strake_stbd_in=(255, 255, 0),
               strake_stbd_tr=(255, 255, 0), strake_port_in=(255, 0, 0), top=(0, 255, 0), rudder=(0, 255, 255), keel_l=(255, 0, 255),
               keel_r=(255, 0, 255), keel_bot=(255, 0, 255), knuckle=(255, 128, 0), bt_top=(0, 255, 0),
               cream=(255, 255, 255), sil_l=(0, 255, 255), sil_r=(0, 255, 255))
    for k, cl in col.items():
        for p in out[k]:
            if k in ("keel_l", "keel_r"):
                uu, vv = p[1], p[0]
            else:
                uu, vv = p[0], p[1]
            d.ellipse([uu - 2, vv - 2, uu + 2, vv + 2], fill=cl)
    im.save(sys.argv[1])
