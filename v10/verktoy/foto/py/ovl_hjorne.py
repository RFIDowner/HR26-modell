"""Sammenligningsbilde paa IMG_9391 (13.11.2026 kveld): eierens blaa prikker
paa akterspeilets hjoerne, modellens hjoerne i dag (gul) og etter tilpasningen
(groenn), og omrisset under vann etter tilpasningen (cyan). Kameraet er zc5,
eller KAM9391 (out/cam9391e.json, f.eks. stripe38f: stripens nedre kant
38 mm over DWL som paa siden, IMG_9370).

Kjoeres fra denne mappa: [KAM9391=noekkel] python ovl_hjorne.py TAG|modell UT.png
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import common as c, uwlib as U, hjerte as Hj, photos as PH
import opt_hjorne as OHJ

tag, out = sys.argv[1], sys.argv[2]
cam = PH.CAM91
# foer trinn 4 (commit 19e9b64, trinn 3)
FOER = dict(SECTION_N=[(0.00, 2.4), (0.15, 3.1), (0.30, 3.4), (0.45, 6.0), (0.80, 4.7), (1.00, 5.4)],
            SECTION_DEADRISE=[(0.00, 45.0), (0.127, 15.0), (0.20, 4.0), (0.30, 0.0), (0.45, 4.9), (0.60, 21.5),
                              (0.75, 20.3), (0.90, 15.4), (1.00, 8.5)],
            DEADWOOD_H=[(2900.0, 0.0), (3600.0, 57.2), (5900.0, 57.2), (6800.0, 124.0), (7400.0, 181.8),
                        (7800.0, 198.6), (8000.0, 198.6)],
            DEADWOOD_W=[(5900.0, 163.2), (6800.0, 184.0)])
if tag == "modell":                      # tabellene i hr26/params.py slik de er naa
    over = {}
else:
    fit = json.load(open(c.W + "/out/opt_hjorne_%s.json" % tag))
    over = {k: [tuple(p) for p in v] for k, v in fit["params"].items()}
blue = json.load(open(c.W + "/out/blaa9391.json"))
zg = np.arange(-400.0, 900.0, 5.0)


def corner_px(C, side):
    yz = OHJ.corner_yz(C, zg)
    X = np.c_[[U.transom_x(z, y) for y, z in yz], side * yz[:, 0], yz[:, 1]]
    X = X[yz[:, 0] > 1.0]
    u, v, _ = cam.project(X)
    return [(float(a), float(b)) for a, b in zip(u, v)]


im = Image.open(c.FOTO + "/IMG_9391.jpg").convert("RGB")
d = ImageDraw.Draw(im)
uu, _, _ = cam.project(np.array([[7800.0, 500.0, 0.0], [7800.0, 0.0, 0.0]]))
right = 1.0 if uu[0] > uu[1] else -1.0
lines = {}
for lab, ov, col in (("foer", FOER, (255, 220, 0)), (tag, over, (40, 230, 60))):
    C = Hj.apply(ov)
    PH.c.C = C
    for s in (-1.0, 1.0):
        d.line(corner_px(C, s * right), fill=col, width=5)
V, F = PH.mesh()
rows = np.arange(690.0, 1000.0, 3.0)
lo, hi = U.row_extents(cam, V, F, rows)
for r, a, b in zip(rows, lo, hi):
    if np.isfinite(a):
        for q in (a, b):
            d.ellipse([q - 3, r - 3, q + 3, r + 3], fill=(0, 230, 255))
for k in ("left", "right"):
    for u, v in blue[k]:
        d.ellipse([u - 6, v - 6, u + 6, v + 6], fill=(30, 80, 255), outline=(255, 255, 255), width=2)
im = im.crop((0, 380, 1500, 1060))
try:
    f = ImageFont.truetype("arial.ttf", 30)
except OSError:
    f = ImageFont.load_default()
lab = (("blaa: dine prikker (hjoernet paa baaten)", (90, 140, 255)),
       ("gul: modellens hjoerne foer (trinn 3)", (255, 220, 0)),
       ("groenn: modellens hjoerne, ny form", (40, 230, 60)),
       ("cyan: omrisset under vann, ny form", (0, 230, 255)))
d2 = ImageDraw.Draw(im)
for i, (t, col) in enumerate(lab):
    d2.rectangle([8, 8 + 40 * i, 20 + d2.textlength(t, font=f), 46 + 40 * i], fill=(0, 0, 0))
    d2.text((14, 10 + 40 * i), t, fill=col, font=f)
im = im.resize((im.width * 2 // 3, im.height * 2 // 3), Image.LANCZOS)
im.save(out)
print(im.size)
