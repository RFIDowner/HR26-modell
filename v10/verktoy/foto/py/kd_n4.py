"""Dekkskanten i «nye (4)» (babord side paa land): modellens linjer projisert
med hovedkameraet (n4_fprof.json, pin_Nc_f850) paa et forstoerret utsnitt.

  python ../../../../tools/memcap.py --gb 3 -- python kd_n4.py [u0 v0 u1 v1 skala] [ut.png]
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

import common as c
import geo9374 as G
import kd_lib as L

IMG = c.FOTO + "/nye4_babord_side.jpg"


def cam_n4(tag="pin_Nc_f850"):
    J = json.load(open(c.W + "/out/n4_fprof.json"))
    d = J["out"][tag]
    q = np.asarray(d["q"], float)
    assert d["cm"] == "pin"
    return G.Cam9374(q[:7], 1170, 831)


def lines(side=-1):
    return dict(
        sheer=(L.sheer3(300.0, 7900.0, 300, side), (255, 40, 40)),
        strake=(L.strake3(450.0, None, 300, side), (255, 140, 0)),
        window=(L.window3(side), (255, 0, 255)),
        coach_foot=(L.coach_foot3(side=side), (0, 200, 255)),
        coach_top=(L.coach_top3(side=side), (0, 255, 120)),
        coaming=(L.coaming_top3(side=side), (255, 255, 0)),
    )


def overlay(cam, img, box, s, out, extra=None, which=None):
    im = Image.open(img).convert("RGB").crop(box)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    dr = ImageDraw.Draw(im)

    def P2(u, v):
        return ((u + 0.5 - box[0]) * s, (v + 0.5 - box[1]) * s)
    for k, (X, col) in lines().items():
        if which and k not in which:
            continue
        u, v, _ = cam.project(X)
        pts = [P2(a, b) for a, b in zip(u, v)]
        for i in range(0, len(pts) - 1, 2):
            dr.line(pts[i:i + 2], fill=col, width=1)
    for X, col in (extra or []):
        u, v, _ = cam.project(np.asarray(X, float))
        for a, b in zip(u, v):
            x, y = P2(a, b)
            dr.ellipse([x - 2, y - 2, x + 2, y + 2], outline=col)
    im.save(out)
    print("skrev", out, im.size)


if __name__ == "__main__":
    cam = cam_n4()
    a = sys.argv[1:]
    box = tuple(int(v) for v in a[:4]) if len(a) >= 5 else (150, 280, 1030, 440)
    s = float(a[4]) if len(a) >= 5 else 2.0
    out = a[5] if len(a) >= 6 else c.W + "/out/kd_n4_ovl.png"
    # marker hver halve meter langs dekkskanten
    xs = np.arange(3000.0, 7900.0, 500.0)
    M = np.array([(x, -C, z) for x, C, z in [(x, L.C.deck_half_breadth(x), L.C.sheer_z(x)) for x in xs]])
    overlay(cam, IMG, box, s, out, extra=[(M, (255, 255, 255))])
    u, v, _ = cam.project(M)
    for x, a_, b_ in zip(xs, u, v):
        print("x %5.0f  u %6.1f v %6.1f  sheer %.0f strake %.0f" % (x, a_, b_, L.C.sheer_z(x), L.C.strake_z(x)))
