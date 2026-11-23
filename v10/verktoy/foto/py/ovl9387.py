"""Overlegg for IMG_9387: foto, sporet forkropp (hvite prikker), dagens modells
omriss med kameraet cam9387 (cyan: skroget uten kjol; magenta: kjolen;
gul: stripens nedre kant paa modellen) -> v10/rapporter/13nov_kveld/forkropp_9387.png
Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python ovl9387.py [utfil]
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import common as c
import uwlib as U
import geo9387 as G
import e9387 as E
import photos

OUT = sys.argv[1] if len(sys.argv) > 1 else c.REPO + "/v10/rapporter/13nov_kveld/forkropp_9387.png"
X0, Y0, X1, Y1 = 0, 420, 1500, 1080
SS = 2          # tegn i dobbel opploesning, skaler ned til slutt


def main():
    cam = E.CAM
    V, F = photos.mesh()
    VK, FK = G.keel_mesh()
    im = Image.open(c.FOTO + "/IMG_9387.jpg").convert("RGB").crop((X0, Y0, X1, Y1))
    im = im.resize(((X1 - X0) * SS, (Y1 - Y0) * SS), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    tp = lambda u, v: ((u - X0) * SS, (v - Y0) * SS)

    def poly(pts, col, w=2):
        pts = [tp(a, b) for a, b in pts if np.isfinite(a) and np.isfinite(b)]
        if len(pts) > 1:
            d.line(pts, fill=col, width=w * SS // 2 + 1)

    # modellens skrog: venstre kant per rad (stevn) og nederste per kolonne (bunn)
    rows = np.arange(440.0, 760.0, 1.0)
    lo, _ = U.row_extents(cam, V, F, rows)
    cols = np.arange(0.0, 1500.0, 2.0)
    _, hi = U.row_extents(cam, V, F, cols, axis="col")
    # sett sammen til ett omriss: stevnen ned til der bunnen tar over
    stem = [(a, b) for a, b in zip(lo, rows) if np.isfinite(a)]
    bot = [(a, b) for a, b in zip(cols, hi) if np.isfinite(b) and a >= (stem[-1][0] if stem else 0)]
    poly(stem, (0, 255, 255), 3)
    poly(bot, (0, 255, 255), 3)
    # kjolen
    kr = np.arange(760.0, 1060.0, 1.0)
    klo, khi = U.row_extents(cam, VK, FK, kr)
    kc = np.arange(900.0, 1450.0, 2.0)
    _, kb = U.row_extents(cam, VK, FK, kc, axis="col")
    poly([(a, b) for a, b in zip(klo, kr)], (255, 0, 255), 2)
    poly([(a, b) for a, b in zip(khi, kr)], (255, 0, 255), 2)
    poly([(a, b) for a, b in zip(kc, kb)], (255, 0, 255), 2)
    # stripens nedre kant paa modellen
    X = E._zline(V, F, E.z_red, xmax=7000.0)
    u, v, _ = cam.project(X)
    o = np.argsort(u)
    poly(list(zip(u[o], v[o])), (255, 230, 0), 1)

    # sporet omriss
    r = 2.2 * SS / 2 + 1
    for vv, uu in E.FRONT:
        a, b = tp(uu, vv); d.ellipse([a - r, b - r, a + r, b + r], fill=(255, 255, 255))
    for uu, vv in E.BOT:
        a, b = tp(uu, vv); d.ellipse([a - r, b - r, a + r, b + r], fill=(255, 255, 255))
    for vv, uu in np.asarray(E._T["root_rows"], float):
        a, b = tp(uu, vv); d.ellipse([a - r, b - r, a + r, b + r], fill=(255, 255, 255))
    for uu, vv in np.asarray(E._T["root_cols"], float):
        a, b = tp(uu, vv); d.ellipse([a - r, b - r, a + r, b + r], fill=(255, 255, 255))
    for uu, vv in E.BTR[::3]:
        a, b = tp(uu, vv); d.ellipse([a - r * 0.7, b - r * 0.7, a + r * 0.7, b + r * 0.7], fill=(255, 255, 255))

    W = 1000
    im = im.resize((W, int(im.size[1] * W / im.size[0])), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
    except OSError:
        f = ImageFont.load_default()
    rf, rb = E.parts(V, F)
    ka, kb = E.keelroot(V, F)
    txt = ["IMG_9387 - kamera fra liste, stevn, kjol, ror og stripe aktenfor x 3 800",
           "hvitt: sporet omriss + stripens nedre kant   cyan: dagens skrog (uten kjol)",
           "magenta: kjolen   gult: modellens stripekant (z %.0f med dette kameraet)" % float(E.z_red(2000.0)),
           "stevn/forfot %+.1f px, bunn %+.1f px, kjolrot rad 800-860 %+.1f px (+ = modellen utenfor)"
           % (rf.mean(), rb.mean(), ka.mean())]
    y = 6
    for t in txt:
        d.text((9, y + 1), t, fill=(0, 0, 0), font=f)
        d.text((8, y), t, fill=(255, 255, 255), font=f)
        y += 18
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    im.save(OUT)
    print("lagret", OUT, im.size)


if __name__ == "__main__":
    main()
