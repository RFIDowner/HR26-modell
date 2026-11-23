"""Overlegg for «nye (6).jpeg»: bildet, modellens omriss med valgt kamera og
de sporede punktene, med tegnforklaring. Lager
v10/rapporter/13nov_nye/n6_overlay.png (1600 px bred).

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 --lock -- python n6_ovl.py [kameravariant]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import common as c
import uwlib as U
import n6_geo as N
import n6_cam as K
import n6_trace as TR

MODE = sys.argv[1] if len(sys.argv) > 1 else None
J = json.load(open(c.W + "/out/n6_cam.json"))
MODE = MODE or J.get("main", "k1_keel")
d = J["modes"][MODE]
cam = K.make_cam(np.asarray(d["q"], float), d["cfg"]["mode"])

BOX = (0, 540, 1170, 1330)
SC = 1600.0 / (BOX[2] - BOX[0])
im = Image.open(TR.IMG).convert("RGB").crop(BOX)
im = im.resize((1600, int(round((BOX[3] - BOX[1]) * SC))), Image.LANCZOS)
im = Image.blend(im, Image.new("RGB", im.size, (255, 255, 255)), 0.25)
dr = ImageDraw.Draw(im)


def tp(u, v):
    return ((np.asarray(u) - BOX[0]) * SC, (np.asarray(v) - BOX[1]) * SC)


def line3(X, col, w=3):
    u, v, z = cam.project(X)
    ok = z > 100
    a, b = tp(u[ok], v[ok])
    dr.line(list(zip(a, b)), fill=col, width=w)


def outline(V, F, col, step=1.0, rows=(560.0, 1330.0), cols=(0.0, 1170.0), r=1.6):
    rr = np.arange(rows[0], rows[1], step)
    lo, hi = U.row_extents(cam, V, F, rr)
    for arr_ in (lo, hi):
        ok = np.isfinite(arr_)
        a, b = tp(arr_[ok], rr[ok])
        for x, y in zip(a, b):
            dr.ellipse([x - r, y - r, x + r, y + r], fill=col)
    cc = np.arange(cols[0], cols[1], step)
    lo, hi = U.row_extents(cam, V, F, cc, axis="col")
    for arr_ in (lo, hi):
        ok = np.isfinite(arr_)
        a, b = tp(cc[ok], arr_[ok])
        for x, y in zip(a, b):
            dr.ellipse([x - r, y - r, x + r, y + r], fill=col)


C_HULL, C_KEEL, C_RUD, C_STR, C_COR, C_WIN, C_TR = ((255, 210, 0), (0, 200, 255), (230, 0, 230), (0, 220, 0),
                                                     (255, 120, 0), (40, 90, 255), (255, 0, 0))
VH, FH = N.hull_mesh(220, 60)
outline(VH, FH, C_HULL, step=2.0)
outline(K.VK, K.FK, C_KEEL, step=1.0, rows=(1040.0, 1330.0), cols=(560.0, 980.0))
VR, FR = N.rudder_mesh()
outline(VR, FR, C_RUD, step=1.0, rows=(900.0, 1330.0), cols=(40.0, 420.0))
line3(K.NEAR3, C_STR)
line3(K.FAR3, C_STR)
line3(K.CORNER3, C_COR)
line3(N.window_outline(), C_WIN)

T = K.T


def dots(pts, col, r=2.2):
    a, b = tp(pts[:, 0], pts[:, 1])
    for x, y in zip(a, b):
        dr.ellipse([x - r, y - r, x + r, y + r], outline=(0, 0, 0), fill=col)


for k in ("strake", "strake_tr"):
    p = np.asarray(T[k], float)[::4]
    dots(np.c_[p[:, 0], p[:, 3]], C_TR)
for k in ("keel_le", "keel_te", "rud_te", "rud_le"):
    p = np.asarray(T[k], float)[::4]
    dots(p[:, ::-1], C_TR)
for k in ("keel_bot", "aft_bot", "rud_bot", "rud_step"):
    p = np.asarray(T[k], float)[::4]
    dots(p, C_TR)
dots(np.asarray(T["tr_corner"], float)[::3, :2], C_TR)
w = T["window"]
dots(np.array([w["aft_end"], w["aft_top"], w["aft_bot"], w["fwd_top"], w["fwd_end"]], float), (255, 255, 255), r=4)

try:
    font = ImageFont.truetype("arial.ttf", 22)
    fs = ImageFont.truetype("arial.ttf", 17)
except OSError:
    font = fs = ImageFont.load_default()
items = [(C_HULL, "skrogets omriss (modell)"), (C_KEEL, "kjol (modell)"), (C_RUD, "ror (modell)"),
         (C_STR, "fenderlist, side og akterspeil (modell)"), (C_COR, "akterspeilets hjoerne (modell)"),
         (C_WIN, "vindu (modell)"), (C_TR, "sporet i bildet"), ((255, 255, 255), "vindusender (haandlest)")]
x0, y0 = 1080, 760
dr.rectangle([x0 - 12, y0 - 44, x0 + 510, y0 + 30 * len(items) + 6], fill=(255, 255, 255), outline=(0, 0, 0))
dr.text((x0, y0 - 38), "nye (6).jpeg - kamera %s" % MODE, fill=(0, 0, 0), font=font)
for i, (col, txt) in enumerate(items):
    y = y0 + 30 * i
    dr.rectangle([x0, y + 4, x0 + 30, y + 20], fill=col, outline=(0, 0, 0))
    dr.text((x0 + 42, y + 1), txt, fill=(0, 0, 0), font=fs)
q = d["q"]
rms = J["modes"][MODE].get("rms", {})
dr.text((20, 16), "C = (%.0f, %.0f, %.0f) mm, f %.0f px, rms %s" % (
    q[0], q[1], q[2], q[6], {k: round(v, 1) for k, v in rms.items() if k != "prior"}), fill=(0, 0, 0), font=fs)
os.makedirs(c.REPO + "/v10/rapporter/13nov_nye", exist_ok=True)
im.save(c.REPO + "/v10/rapporter/13nov_nye/n6_overlay.png")
print("lagret", im.size)
