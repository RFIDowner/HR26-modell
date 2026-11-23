"""Hjelpebilde for IMG_9389: modellens trekk projisert med et kamera p
(standard: score.py sitt omtrentlige). Bruk: python proj9389.py [p-json] [ut.png] [x0 y0 x1 y1]"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

import common as c
import uwlib as U
import geo9389 as G

P, C = c.P, c.C
W_, H_ = 2000, 1500
P_SCORE = [1202.9, 1570.5, -523.5, -30.0, 2.62, -3.55, 1563.4]


def draw(p, out, crop=None, scale=1.0, extra=None):
    cam = U.Cam(p, W_, H_)
    im = Image.open(c.FOTO + "/IMG_9389.jpg").convert("RGB")
    d = ImageDraw.Draw(im)

    def poly(X, col, w=2):
        u, v, z = cam.project(X)
        ok = z > 100
        pts = list(zip(u[ok], v[ok]))
        if len(pts) > 1:
            d.line(pts, fill=col, width=w)

    def dots(pts, col, r=2):
        for a, b in pts:
            if np.isfinite(a) and np.isfinite(b):
                d.ellipse([a - r, b - r, a + r, b + r], fill=col)

    V, F = U.hull_mesh(200, 50)
    dots(G.mesh_outline_px(cam, V, F, 3), (0, 255, 255), 1)
    VK, FK = G.keel_mesh()
    dots(G.mesh_outline_px(cam, VK, FK, 3), (255, 0, 255), 1)
    VR, FR = G.rudder_mesh()
    dots(G.mesh_outline_px(cam, VR, FR, 3), (255, 128, 0), 1)
    poly(G.strake3(300.0), (255, 255, 0), 2)
    poly(G.zline3(G.bt_top_z, 500, P.LOA, 200), (0, 0, 255), 2)
    poly(G.zline3(lambda x: 38.0, 500, P.LOA, 200), (0, 255, 0), 2)
    poly(G.window_lower3(), (255, 255, 255), 2)
    poly(G.transom_corner3(), (255, 0, 0), 2)
    poly(G.stem_top3(), (255, 255, 255), 2)
    # stasjonsmerker langs listen
    for x in range(1000, 8000, 500):
        X = np.array([[x, G.side_y(x, C.strake_z(x)) + 13, C.strake_z(x)], [x, G.side_y(x, 38.0), 38.0]])
        u, v, z = cam.project(X)
        if (z > 100).all():
            d.line(list(zip(u, v)), fill=(255, 255, 255), width=1)
            d.text((u[1] + 3, v[1] + 3), str(x), fill=(255, 255, 255))
    if extra is not None:
        extra(d, cam)
    if crop:
        im = im.crop(crop)
    if scale != 1.0:
        im = im.resize((int(im.size[0] * scale), int(im.size[1] * scale)), Image.LANCZOS)
    im.save(out)


if __name__ == "__main__":
    p = P_SCORE
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        j = json.load(open(sys.argv[1]))
        p = j["p"] if isinstance(j, dict) else j
    out = sys.argv[2] if len(sys.argv) > 2 else "proj9389.png"
    crop = tuple(int(a) for a in sys.argv[3:7]) if len(sys.argv) > 6 else None
    draw(p, out, crop, 0.5 if crop is None else 1.0)
