"""Akterspeilets hjoerne (kanten mot skrogsiden) paa IMG_9391, 13.11.2026 kveld.

Eieren tegnet blaa prikker paa hjoernet/boeyen i ovl_hjerte.png; de ligger i
out/blaa9391.json (IMG_9391-piksler). Her projiseres modellens hjoerne med
zc5-kameraet:
  * K: der skrogsiden moeter akterspeilsflaten (hull._corner), skarp kant
    under TRANSOM_CORNER_Z[0];
  * T og E: rundingens tangentpunkt paa akterspeilet og endepunkt paa siden
    (hull._stern_plan), der hjoernet er rundet.
Prikkene tilbakeprojiseres ogsaa til akterspeilsflaten, saa avviket kan
oppgis i mm (halvbredde y ved samme hoeyde z).

Kjoeres fra denne mappa: python hjorne9391.py [UT.png]
"""
import json
import math
import sys

import numpy as np
from scipy.optimize import brentq

import common as c, uwlib as U
from hr26 import hull as H

P, C = c.P, c.C
import os
KAM = os.environ.get("KAM9391", "")       # tom: zc5; ellers en noekkel i out/cam9391e.json
if KAM:
    cam = U.Cam(json.load(open(c.W + "/out/cam9391e.json"))[KAM]["p"][:7], 1500, 2000)
else:
    cam = U.Cam(json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"][:7], 1500, 2000)
SUF = "_" + KAM if KAM else ""
blue = json.load(open(c.W + "/out/blaa9391.json"))


def ray(u, v):
    d = np.array([(u - cam.cx) / cam.f, (v - cam.cy) / cam.f, 1.0]) @ cam.R
    return cam.C, d / np.linalg.norm(d)


def on_transom(u, v):
    """Punktet paa akterspeilsflaten x = transom_x(z, y) som ses i (u, v)."""
    o, d = ray(u, v)
    g = lambda t: (o + t * d)[0] - U.transom_x((o + t * d)[2], (o + t * d)[1])
    ts = np.linspace(500.0, 4000.0, 200)
    gv = [g(t) for t in ts]
    for i in range(len(ts) - 1):
        if gv[i] * gv[i + 1] <= 0.0:
            t = brentq(g, ts[i], ts[i + 1])
            return o + t * d
    return None


# --- modellens hjoerne -------------------------------------------------------
zs = np.arange(-420.0, 1000.0, 5.0)
K, T, E = [], [], []
for z in zs:
    k = H._corner(float(z))
    if k is not None:
        K.append((k[0], k[1], z))
    pl = H._stern_plan(float(z))
    if pl is not None and z > P.TRANSOM_CORNER_Z[0]:
        yt, R, a = pl
        if yt < (k[1] if k is not None else 1e9) - 1.0:
            T.append((C.transom_x(float(z), yt), yt, z))
            (ex, ey), _ = H._arc_point(float(z), yt, R, a)
            E.append((ex, ey, z))
K, T, E = (np.array(a) for a in (K, T, E))
zK = K[:, 2]


def mirror(A):
    return np.vstack([A, A * [1, -1, 1]])


def proj(A, side):
    A = A.copy()
    A[:, 1] *= side
    u, v, _ = cam.project(A)
    return np.c_[u, v]


# babord (y < 0) ser til hoeyre i bildet? Avgjoer med et punkt.
uu, _, _ = cam.project(np.array([[7800.0, 500.0, 0.0]]))
SIDE_RIGHT = 1.0 if uu[0] > cam.project(np.array([[7800.0, 0.0, 0.0]]))[0][0] else -1.0

res = {"left": [], "right": []}
for key, side in (("left", -SIDE_RIGHT), ("right", SIDE_RIGHT)):
    pk = proj(K, side)
    for u, v in blue[key]:
        X = on_transom(u, v)
        yb, zb = abs(X[1]), X[2]
        ym = float(np.interp(zb, zK, K[:, 1]))
        yT = float(np.interp(zb, T[:, 2], T[:, 1])) if len(T) and T[0, 2] <= zb <= T[-1, 2] else None
        # naermeste avstand i bildet til modellens hjoernelinje K
        dpx = float(np.min(np.hypot(pk[:, 0] - u, pk[:, 1] - v)))
        # mm per piksel paa akterspeilet her
        X2 = on_transom(u + 1.0, v)
        mmpx = float(np.linalg.norm(X2 - X))
        res[key].append(dict(u=u, v=v, z=float(zb), y_photo=float(yb), y_model=ym,
                             y_tangent=yT, dy=float(yb - ym), dpx=dpx, mmpx=mmpx))

print(f"modellens hjoerne: z {zK.min():.0f}..{zK.max():.0f}, foten (y<5) ved z ~ "
      f"{zK[np.argmax(K[:, 1] > 5)]:.0f}")
for key in ("left", "right"):
    print(f"--- {key} ---  z   y_foto  y_modell  y_tangent  dy(mm)  dpx  mm/px")
    for r in res[key]:
        t = f"{r['y_tangent']:7.0f}" if r["y_tangent"] is not None else "      -"
        print(f"  ({r['u']:6.0f},{r['v']:5.0f})  {r['z']:6.0f}  {r['y_photo']:6.0f}  {r['y_model']:7.0f}  {t}"
              f"  {r['dy']:+6.0f}  {r['dpx']:4.1f}  {r['mmpx']:4.1f}")
for z in (-400, -350, -300, -250, -200, -150, -100, -50, 0, 100, 200, 300, 400, 500, 600, 700, 800):
    print(f"z {z:5d}: modell y {np.interp(z, zK, K[:, 1]):6.0f}")
c.save_json(dict(res=res, K=K, T=T, E=E, side_right=SIDE_RIGHT), c.W + "/out/hjorne9391%s.json" % SUF)

if len(sys.argv) > 1:
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(c.FOTO + "/IMG_9391.jpg").convert("RGB")
    d = ImageDraw.Draw(im)
    for side in (-1.0, 1.0):
        for A, col, w in ((K, (255, 230, 0), 4), (T, (0, 230, 255), 3), (E, (255, 0, 255), 3)):
            if len(A) == 0:
                continue
            p = proj(A, side)
            d.line([tuple(q) for q in p], fill=col, width=w)
    for key in ("left", "right"):
        for u, v in blue[key]:
            d.ellipse([u - 5, v - 5, u + 5, v + 5], fill=(30, 90, 255), outline=(255, 255, 255))
    im = im.crop((250, 420, 1250, 1000))
    try:
        f = ImageFont.truetype("arial.ttf", 26)
    except OSError:
        f = ImageFont.load_default()
    lab = (("blaa: eierens prikker (hjoernet paa baaten)", (60, 120, 255)),
           ("gul: modellens hjoerne (akterspeil moeter siden)", (255, 230, 0)),
           ("cyan/magenta: modellens runding (start/slutt)", (0, 230, 255)))
    for i, (t, col) in enumerate(lab):
        d2 = ImageDraw.Draw(im)
        d2.rectangle([8, 8 + 36 * i, 18 + d2.textlength(t, font=f), 40 + 36 * i], fill=(0, 0, 0))
        d2.text((13, 10 + 36 * i), t, fill=col, font=f)
    im.save(sys.argv[1])
    print(im.size)
