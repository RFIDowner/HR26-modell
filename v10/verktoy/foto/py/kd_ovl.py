"""Modellens linjer (dekkskant roed, liste oransje, vindu magenta, ruffens fot
cyan, takkant groenn, karm gul) projisert med et loest kamera paa et
forstoerret utsnitt. Hvite ringer: dekkskanten hver 0,5 m fra x 3 000.

  python ../../../../tools/memcap.py --gb 3 -- python kd_ovl.py n4|n6|9387|9374 u0 v0 u1 v1 skala ut.png
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

import common as c
import kd_lib as L
import kd_render as KR

IMGS = {"n4": c.FOTO + "/nye4_babord_side.jpg", "n6": c.FOTO + "/nye6_akterhjorne.jpg",
        "9387": c.FOTO + "/IMG_9387.jpg", "9374": c.FOTO + "/IMG_9374.jpg"}
SIDE = {"n4": -1, "n6": +1, "9387": -1, "9374": -1}


def model_lines(side):
    return [
        (L.sheer3(300.0, 7900.0, 300, side), (255, 40, 40)),
        (L.strake3(450.0, None, 300, side), (255, 140, 0)),
        (L.window3(side), (255, 0, 255)),
        (L.coach_foot3(side=side), (0, 200, 255)),
        (L.coach_top3(side=side), (0, 255, 120)),
        (L.coaming_top3(side=side), (255, 255, 0)),
    ]


def overlay(name, box, s, out, extra=()):
    cam, W, H = KR.cam_named(name)
    side = SIDE[name]
    im = Image.open(IMGS[name]).convert("RGB").crop(box)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    dr = ImageDraw.Draw(im)

    def P2(u, v):
        return ((u + 0.5 - box[0]) * s, (v + 0.5 - box[1]) * s)
    for X, col in model_lines(side):
        u, v, _ = cam.project(X)
        pts = [P2(a, b) for a, b in zip(u, v)]
        for i in range(0, len(pts) - 1, 2):
            dr.line(pts[i:i + 2], fill=col, width=1)
    xs = np.arange(3000.0, 7900.0, 500.0)
    M = np.array([(x, side * L.C.deck_half_breadth(x), L.C.sheer_z(x)) for x in xs])
    u, v, _ = cam.project(M)
    for x, a, b in zip(xs, u, v):
        X, Y = P2(a, b)
        dr.ellipse([X - 3, Y - 3, X + 3, Y + 3], outline=(255, 255, 255))
        print("x %5.0f  u %7.1f v %7.1f" % (x, a, b))
    for pts, col in extra:
        for a, b in pts:
            X, Y = P2(a, b)
            dr.ellipse([X - 2, Y - 2, X + 2, Y + 2], fill=col)
    im.save(out)
    print("skrev", out, im.size)
    return cam


if __name__ == "__main__":
    a = sys.argv[1:]
    overlay(a[0], tuple(int(v) for v in a[1:5]), float(a[5]), a[6])
