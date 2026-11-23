"""Overlegg paa «nye (1).jpeg» med et kamera fra out/n1_cam.json:
modellens fenderliste, akterspeilets overkant, akterspeilhjoernet (gult),
kjolen og skrogets omriss (cyan), og sporene fra bildet (n1_trace.json).

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python n1_ovl.py VARIANT UT.png [kort]
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import common as c
import uwlib as U
import n1_geo as N
import n1_cam as K

P, C = N.P, N.C
var, out = sys.argv[1], sys.argv[2]
short = len(sys.argv) > 3
J = json.load(open(c.W + "/out/n1_cam.json"))["modes"][var]
cam = N.make_cam(np.array(J["q"]), J["mode"], K.W_, K.H_)
T = K.T

im = Image.open(K.N1 if hasattr(K, "N1") else r"C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/nye (1).jpeg").convert("RGB")
d = ImageDraw.Draw(im)


def line(X, col, w=3):
    u, v, z = cam.project(X)
    pts = [(float(a), float(b)) for a, b, zz in zip(u, v, z) if zz > 100]
    if len(pts) > 1:
        d.line(pts, fill=col, width=w)


F = K.model_feats()
for k in ("strake_port", "strake_port_tr", "strake_stbd_tr"):
    line(F[k], (255, 230, 0), 3)
line(N.strake_side(1.0), (255, 230, 0), 3)
line(F["top"], (0, 255, 0), 3)
# akterspeilhjoernet (modellen) paa begge sider
for s in (-1.0, 1.0):
    line(N.corner_line(-420.0, None, 10.0, s), (255, 140, 0), 4)
# akterspeilet i noen hoeyder (tvers over, mellom hjoernene)
for z in (150.0, 100.0, 38.0, 0.0):
    k = N.corner_y(z)
    if k is None:
        continue
    ys = np.linspace(-k[1], k[1], 30)
    line(np.c_[[C.transom_x(z, y) for y in ys], ys, np.full(30, z)], (255, 255, 255), 1)
# skrogets omriss og kjolen
V, Fh = N.hull_mesh()
rows = np.arange(1100.0, 1860.0, 4.0)
lo, hi = U.row_extents(cam, V, Fh, rows)
for r, a, b in zip(rows, lo, hi):
    if np.isfinite(a):
        d.ellipse([a - 2, r - 2, a + 2, r + 2], fill=(0, 230, 255))
        d.ellipse([b - 2, r - 2, b + 2, r + 2], fill=(0, 230, 255))
rows = np.arange(1700.0, 2100.0, 3.0)
lo, hi = U.row_extents(cam, K.VK, K.FK, rows)
for r, a, b in zip(rows, lo, hi):
    if np.isfinite(a):
        d.ellipse([a - 2, r - 2, a + 2, r + 2], fill=(255, 0, 255))
        d.ellipse([b - 2, r - 2, b + 2, r + 2], fill=(255, 0, 255))
cols = np.arange(440.0, 600.0, 3.0)
lo, hi = U.row_extents(cam, K.VK, K.FK, cols, axis="col")
for cc, a, b in zip(cols, lo, hi):
    if np.isfinite(b):
        d.ellipse([cc - 2, b - 2, cc + 2, b + 2], fill=(255, 0, 255))
line(N.rudder_le(), (0, 255, 255), 2)
# spor (smaa hvite prikker)
if short:
    for k in ("knuckle", "bt_top", "cream"):
        for p in T[k]:
            d.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], fill=(255, 255, 255))
if not short:
    for k in ("strake_port", "strake_port_in", "strake_port_tr", "strake_stbd_in", "strake_stbd_tr", "top", "knuckle",
              "bt_top", "cream"):
        for p in T[k]:
            d.ellipse([p[0] - 1.5, p[1] - 1.5, p[0] + 1.5, p[1] + 1.5], fill=(255, 255, 255))
    for k in ("keel_l", "keel_r"):
        for p in T[k]:
            d.ellipse([p[1] - 1.5, p[0] - 1.5, p[1] + 1.5, p[0] + 1.5], fill=(255, 255, 255))
    for p in T["keel_bot"]:
        d.ellipse([p[0] - 1.5, p[1] - 1.5, p[0] + 1.5, p[1] + 1.5], fill=(255, 255, 255))
# rorets nederste punkt i bildet og modellens (forkant/bunn -1 094 og Enderlein -1 047)
d.ellipse([688 - 7, 1547 - 7, 688 + 7, 1547 + 7], outline=(255, 255, 255), width=3)
for zb, col in ((-1094.0, (0, 255, 255)), (-1047.0, (255, 80, 80))):
    u, v, _ = cam.project(np.array([[C.transom_x(zb, 0.0) + P.RUDDER_GAP, 0.0, zb]]))
    d.ellipse([u[0] - 7, v[0] - 7, u[0] + 7, v[0] + 7], outline=col, width=3)
if short:
    im = im.crop((0, 450, 1170, 2150))
    try:
        f = ImageFont.truetype("arial.ttf", 30)
    except OSError:
        f = ImageFont.load_default()
    lab = (("nye (1) mot modellen (kamera %s)" % var, (255, 255, 255)),
           ("gul: fenderlisten  groenn: akterspeilets overkant", (255, 230, 0)),
           ("oransje: modellens akterspeilhjoerne", (255, 140, 0)),
           ("hvite prikker: hjoernet og stripekantene i bildet", (255, 255, 255)),
           ("cyan: skrogets omriss, roret (forkant)  lilla: kjolen", (0, 230, 255)),
           ("ringer: rorbunn i bildet (hvit), modell -1094 (cyan), -1047 (roed)", (255, 180, 180)))
    d2 = ImageDraw.Draw(im)
    for i, (t, col) in enumerate(lab):
        d2.rectangle([8, 8 + 38 * i, 18 + d2.textlength(t, font=f), 44 + 38 * i], fill=(0, 0, 0))
        d2.text((13, 10 + 38 * i), t, fill=col, font=f)
    im = im.resize((im.width * 3 // 5, im.height * 3 // 5), Image.LANCZOS)
im.save(out)
print(out, im.size)
