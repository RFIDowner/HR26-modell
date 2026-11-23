"""Overlegg paa «nye (3).jpeg» (kamera fra out/n3_cam.json). BILDET VISER FOLK:
skrives bare til den private mappa, aldri i repoet.

Kjoeres fra denne mappa:  python ../../../../tools/memcap.py --gb 3 -- python n3_ovl.py [modus]
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import common as c
import uwlib as U
import n1_geo as N
import n3_cam as K

P, C = N.P, N.C
mode = sys.argv[1] if len(sys.argv) > 1 else "pp"
OUT = r"C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/analyse/n3_overlay_%s.png" % mode
J = json.load(open(c.W + "/out/n3_cam.json"))["modes"][mode]
cam = K.make(np.array(J["q"]), mode)
im = Image.open(r"C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/nye (3).jpeg").convert("RGB")
d = ImageDraw.Draw(im)


def line(X, col, w=3):
    u, v, z = cam.project(X)
    pts = [(float(a), float(b)) for a, b, zz in zip(u, v, z) if zz > 100]
    if len(pts) > 1:
        d.line(pts, fill=col, width=w)


line(K.S3, (255, 230, 0), 3)
for s in (-1.0, 1.0):
    line(N.corner_line(-420.0, None, 10.0, s), (255, 140, 0), 3)
line(N.rudder_le(), (0, 255, 255), 2)
rows = np.arange(1450.0, 1800.0, 3.0)
lo, hi = U.row_extents(cam, K.VK, K.FK, rows)
for r, a, b in zip(rows, lo, hi):
    if np.isfinite(a):
        d.ellipse([a - 2, r - 2, a + 2, r + 2], fill=(255, 0, 255)); d.ellipse([b - 2, r - 2, b + 2, r + 2], fill=(255, 0, 255))
T = K.T
for p in T["knuckle"]:
    d.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], fill=(255, 255, 255))
tu, tv = T["rudder_tip"]
d.ellipse([tu - 7, tv - 7, tu + 7, tv + 7], outline=(255, 255, 255), width=3)
for zb, col in ((-1094.0, (0, 255, 255)), (-1047.0, (255, 80, 80))):
    X = np.array([[C.transom_x(zb, 0.0) + P.RUDDER_GAP, 0.0, zb], [P.RUDDER_TE_X, 0.0, zb]])
    u, v, _ = cam.project(X)
    for a, b in zip(u, v):
        d.ellipse([a - 7, b - 7, a + 7, b + 7], outline=col, width=3)
im = im.crop((0, 900, 1170, 2000))
im.save(OUT)
print(OUT, im.size)
