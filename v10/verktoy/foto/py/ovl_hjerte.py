"""Overlegg paa IMG_9391 (akterfra): sporet roedt omriss (hvitt), modellens
omriss foer trinn 3 (magenta, out/outl_before.json fra kontrollen) og naa (cyan),
med zc5-kameraet. Kjoeres fra denne mappa: python ovl_hjerte.py UT.png
"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import common as c, uwlib as U, photos as PH

cam = U.Cam(json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"][:7], 1500, 2000)
im = Image.open(c.FOTO + "/IMG_9391.jpg").convert("RGB")
d = ImageDraw.Draw(im)
ro = np.array(json.load(open(c.W + "/out/t9391.json"))["red_outline"])
for r, uL, uR in ro:
    for u in (uL, uR):
        d.ellipse([u - 2.5, r - 2.5, u + 2.5, r + 2.5], fill=(255, 255, 255))
rows = np.arange(700.0, 1010.0, 2.0)
old = json.load(open(c.W + "/out/outl_before.json"))["9391"]
for r, a, b in zip(old["rows"], old["lo"], old["hi"]):
    if a is not None and b is not None and np.isfinite(a) and 700 <= r <= 1010:
        d.ellipse([a - 2, r - 2, a + 2, r + 2], fill=(255, 0, 255))
        d.ellipse([b - 2, r - 2, b + 2, r + 2], fill=(255, 0, 255))
V, F = PH.mesh()
lo, hi = U.row_extents(cam, V, F, rows)
for r, a, b in zip(rows, lo, hi):
    if np.isfinite(a):
        d.ellipse([a - 2.5, r - 2.5, a + 2.5, r + 2.5], fill=(0, 230, 255))
        d.ellipse([b - 2.5, r - 2.5, b + 2.5, r + 2.5], fill=(0, 230, 255))
im = im.crop((0, 560, 1500, 1160))
try:
    f = ImageFont.truetype("arial.ttf", 30)
except OSError:
    f = ImageFont.load_default()
for i, (t, col) in enumerate((("hvitt: baatens roede bunn (sporet)", (255, 255, 255)),
                              ("magenta: modellen foer", (255, 0, 255)),
                              ("cyan: modellen naa (hjerteform)", (0, 230, 255)))):
    d2 = ImageDraw.Draw(im)
    d2.rectangle([10, 10 + 40 * i, 20 + d2.textlength(t, font=f), 46 + 40 * i], fill=(0, 0, 0))
    d2.text((15, 12 + 40 * i), t, fill=col, font=f)
im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
im.save(sys.argv[1])
print(im.size)
