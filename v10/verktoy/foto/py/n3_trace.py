"""Spor i «nye (3).jpeg» (1170 x 2532 skjermklipp med svarte felt; baaten paa
bukker, sett rett akterfra i staaende oeyehoeyde). 13.11.2026, akter-maaleren.

BILDET VISER FOLK (to menn til hoeyre): ingen utsnitt eller overlegg av
bildet skrives i repoet. Sjekkbilder gaar til den private mappa
C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/analyse/.

  strake      fenderlisten (moerk) tvers over akterspeilet og et stykke
              forover paa styrbord side, senter per kolonne
  keel_l/r    kjolens venstre/hoeyre kant per rad (roedt mot asfalt/bukker)
  keel_bot    kjolens bunn per kolonne
  knuckle     styrbord akterspeilhjoerne (lys/skygge-grense, hoeypassfiltrert)
  bt_top      vannlinjestripens overkant (hvit -> moerk blaa) per kolonne
  rudder_tip  rorets nederste punkt; rudder_l/r rorets kanter per rad

Kjoeres fra denne mappa:  python ../../../../tools/memcap.py --gb 3 -- python n3_trace.py [sjekk.png]
"""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

import common as c
from n1_trace_lib import dark_center_col, edge_sub, gi       # noqa: E402

SRC = r"C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/nye (3).jpeg"
A = np.asarray(Image.open(SRC).convert("RGB")).astype(float)
H_, W_ = A.shape[:2]
R, G, B = A[..., 0], A[..., 1], A[..., 2]
L = A.mean(2)
Ls = ndi.gaussian_filter(L, 1.2)
out = {"W": W_, "H": H_}

# ---- fenderlisten -------------------------------------------------------------
gs = [(25, 1055), (60, 1050), (100, 1044), (200, 1030), (300, 1019), (350, 1015), (450, 1012), (550, 1013),
      (650, 1024), (700, 1032), (750, 1042), (800, 1052), (850, 1068), (900, 1086), (950, 1100), (985, 1112)]
pts = []
for u in list(range(30, 346, 4)) + list(range(446, 650, 4)) + list(range(672, 986, 4)):
    r = dark_center_col(Ls, u, gi(gs, u), 16)
    if r and 6 <= r[1] <= 26:
        pts.append([u, r[0], r[1]])
out["strake"] = pts

# ---- kjolen ---------------------------------------------------------------------
RED = (R > G + 25) & (R > B + 20)
RED = ndi.binary_opening(RED, iterations=1)
KRED = (R - G > 8) & (R - B > 6) & (L < 90)
KRED = ndi.binary_opening(KRED, iterations=1)
kl, kr = [], []
for v in range(1560, 1742, 4):
    row = KRED[v, 540:720]
    idx = np.where(row)[0]
    if len(idx) < 10:
        continue
    runs = np.split(idx, np.where(np.diff(idx) > 2)[0] + 1)
    run = max(runs, key=len)
    a, b = 540 + run[0], 540 + run[-1]
    ea, _ = edge_sub(Ls[v, a - 5:a + 5]); eb, _ = edge_sub(Ls[v, b - 5:b + 5])
    kl.append([a - 5 + ea, v]); kr.append([b - 5 + eb, v])
kb = []
for u in range(574, 600, 2):
    col = KRED[1690:1790, u]
    idx = np.where(col)[0]
    if len(idx) < 5:
        continue
    runs = np.split(idx, np.where(np.diff(idx) > 2)[0] + 1)
    b = 1690 + runs[0][-1]
    e, _ = edge_sub(Ls[b - 5:b + 6, u])
    kb.append([u, b - 5 + e])
out["keel_l"], out["keel_r"], out["keel_bot"] = kl, kr, kb

# ---- roret ------------------------------------------------------------------------
rl, rr = [], []
for v in range(1400, 1862, 4):
    row = RED[v, 360:520]
    idx = np.where(row)[0]
    if len(idx) < 6:
        continue
    runs = np.split(idx, np.where(np.diff(idx) > 2)[0] + 1)
    run = max(runs, key=len)
    rl.append([360 + run[0], v]); rr.append([360 + run[-1], v])
out["rudder_l"], out["rudder_r"] = rl, rr
col_bottom = []
for u in range(440, 500, 2):
    col = RED[1780:1900, u]
    idx = np.where(col)[0]
    if len(idx):
        col_bottom.append([u, 1780 + idx[-1]])
cb = np.array(col_bottom, float)
k = int(np.argmax(cb[:, 1]))
out["rudder_tip"] = [float(cb[k, 0]), float(cb[k, 1])]
out["rudder_bot"] = col_bottom

# ---- styrbord akterspeilhjoerne ----------------------------------------------------
HP = ndi.gaussian_filter(L, 1.5) - ndi.gaussian_filter(L, 20.0)
HPs = ndi.gaussian_filter(HP, 1.5)
gk_rows = [(1140, 775), (1175, 770), (1215, 755), (1250, 730), (1275, 700)]
gk_cols = [(700, 1275), (665, 1295), (620, 1310), (580, 1322)]
kn = []
for v in range(1140, 1272, 3):
    ug = gi(gk_rows, v)
    lo = int(ug - 12)
    e, gval = edge_sub(HPs[v, lo:lo + 24])
    kn.append([lo + e, v, gval])
for u in range(576, 704, 3):
    vg = gi(gk_cols, u)
    lo = int(vg - 8)
    prof = HPs[lo:lo + 14, u]
    gg = np.gradient(prof)
    k = int(np.argmin(gg))                 # lyst (akterspeilet) over, graatt (laaringen) under
    if 0 < k < len(gg) - 1 and gg[k] < -1.0:
        a_, b_, c_ = gg[k - 1], gg[k], gg[k + 1]
        den = a_ - 2 * b_ + c_
        kn.append([u, lo + k + (0.5 * (a_ - c_) / den if abs(den) > 1e-9 else 0.0), float(gg[k])])
out["knuckle"] = kn

# ---- vannlinjestripens overkant -------------------------------------------------------
bt = []
for u in list(range(160, 360, 4)) + list(range(450, 980, 4)):
    prof = Ls[1300:1400, u]
    g = np.diff(prof)
    k = int(np.argmin(g))          # sterkeste lys -> moerk nedover
    if g[k] < -20:
        e, _ = edge_sub(prof[max(k - 4, 0):k + 6])
        bt.append([u, 1300 + max(k - 4, 0) + e])
out["bt_top"] = bt

c.save_json(out, c.W + "/out/n3_trace.json")
for k_, v_ in out.items():
    if isinstance(v_, list):
        print(f"{k_:12s} {len(v_):4d}")
print("rorets nederste punkt:", out["rudder_tip"])

if len(sys.argv) > 1:
    from PIL import ImageDraw
    im = Image.open(SRC).convert("RGB")
    d = ImageDraw.Draw(im)
    col = dict(strake=(255, 255, 0), keel_l=(255, 0, 255), keel_r=(255, 0, 255), keel_bot=(255, 0, 255),
               rudder_l=(0, 255, 255), rudder_r=(0, 255, 255), knuckle=(255, 128, 0), bt_top=(0, 255, 0),
               rudder_bot=(0, 255, 255))
    for k_, cl in col.items():
        for p in out[k_]:
            d.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], fill=cl)
    im.save(sys.argv[1])
