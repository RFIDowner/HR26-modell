"""Legger modellens kurver (fra snapshot) over tegningen 448-5.

Bruk: python overlay.py <bilde> <ut-prefiks> bow_px s_h q0 s_v plan_cl s_y
  profil: px = bow_px - x / s_h,  py = q0 - z / s_v
  plan:   px = bow_px - x / s_h,  py = plan_cl -+ y / s_y
Kjoeres fra innredning/scripts med snap paa sys.path (ikke -I, men bildet
leses bare som data)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "snap"))

import numpy as np
from PIL import Image, ImageDraw

from hr26 import curves as C, params as P, deckhouse as D

src, pre = sys.argv[1], sys.argv[2]
bow, sh, q0, sv, pcl, sy = [float(v) for v in sys.argv[3:9]]
im = Image.open(src).convert("RGB")
d = ImageDraw.Draw(im)

def pxy(x, z):
    return (bow - x / sh, q0 - z / sv)

def pl(x, y):
    return (bow - x / sh, pcl - y / sy)

def poly(pts, col, w=1):
    d.line(pts, fill=col, width=w)

xs = np.linspace(0, 7950, 400)
poly([pxy(x, C.sheer_z(x)) for x in xs], (255, 0, 0))
poly([pxy(x, C.deck_z(x, 0)) for x in xs], (255, 120, 0))
poly([pxy(x, C.bottom_z(x)) for x in xs], (255, 0, 0))
poly([pxy(x, C.strake_z(x)) for x in xs], (0, 160, 0))
xr = np.linspace(P.STEP_X0, P.COACH_X1, 200)
poly([pxy(x, D.roof_z(x)) for x in xr], (255, 0, 255))
# ruffens front og akterkant
poly([pxy(P.STEP_X0, C.deck_z(P.STEP_X0, 0)), pxy(P.STEP_X1, D.roof_z(P.STEP_X1))], (255, 0, 255))
poly([pxy(P.COACH_X1, C.deck_z(P.COACH_X1, 0)), pxy(P.COACH_X1, D.roof_z(P.COACH_X1))], (255, 0, 255))
# mast
for xm in (P.MAST_STEP_X - 60, P.MAST_STEP_X + 60):
    poly([pxy(xm, D.roof_z(P.MAST_STEP_X)), pxy(xm, D.roof_z(P.MAST_STEP_X) + 400)], (0, 0, 255))
# kjol
k = [(P.KEEL_LE_ROOT, C.bottom_z(P.KEEL_LE_ROOT)), (P.KEEL_LE_TIP, -P.DRAFT), (P.KEEL_TE_TIP, -P.DRAFT), (P.KEEL_TE_ROOT, C.bottom_z(P.KEEL_TE_ROOT))]
poly([pxy(*p) for p in k], (0, 0, 255))
# akterspeil
zt = np.linspace(-250, 1000, 20)
poly([pxy(C.transom_x(z), z) for z in zt], (255, 0, 0))
# DWL
poly([pxy(-200, 0), pxy(8300, 0)], (0, 200, 200))
# vindu
xw = np.linspace(P.WIN_X0, P.WIN_X1, 40)
poly([pxy(x, C.strake_z(x) + P.WIN_ABOVE_STRAKE) for x in xw] + [pxy(x, C.sheer_z(x) - P.WIN_BELOW_DECK) for x in xw[::-1]] + [pxy(xw[0], C.strake_z(xw[0]) + P.WIN_ABOVE_STRAKE)], (0, 160, 0))
# cockpit
poly([pxy(P.COCKPIT_X0, P.COCKPIT_FLOOR_Z), pxy(7700, P.COCKPIT_FLOOR_Z)], (0, 0, 255))
xc = np.linspace(5680, 6800, 30)
poly([pxy(x, D.coaming_top_z(x)) for x in xc], (0, 0, 255))

# plan
xp = np.linspace(0, 7891, 400)
poly([pl(x, C.deck_half_breadth(x)) for x in xp], (255, 0, 0))
poly([pl(x, -C.deck_half_breadth(x)) for x in xp], (255, 0, 0))
xcp = np.linspace(P.STEP_X0, P.COACH_X1, 200)
poly([pl(x, D.coach_half_width(x)) for x in xcp], (255, 0, 255))
poly([pl(x, -D.coach_half_width(x)) for x in xcp], (255, 0, 255))
poly([pl(P.COACH_X1, D.coach_half_width(P.COACH_X1)), pl(P.COACH_X1, -D.coach_half_width(P.COACH_X1))], (255, 0, 255))
# luker
for (a, b, w, h) in (P.FOREHATCH, P.SLIDE_HATCH):
    poly([pl(a, w / 2), pl(b, w / 2), pl(b, -w / 2), pl(a, -w / 2), pl(a, w / 2)], (0, 0, 255))
# cockpit
xq = np.linspace(P.COCKPIT_X0, 7640, 60)
poly([pl(x, D.cockpit_half_width(x)) for x in xq], (0, 0, 255))
poly([pl(x, -D.cockpit_half_width(x)) for x in xq], (0, 0, 255))
d.ellipse([pl(P.MAST_STEP_X, 60)[0] - 4, pl(0, 60)[1] - 4, pl(P.MAST_STEP_X, 60)[0] + 4, pl(0, 60)[1] + 4], outline=(0, 0, 255))

im.crop((150, 100, 2400, 900)).save(pre + "_profil.png")
im.crop((300, 960, 2300, 1720)).save(pre + "_plan.png")
small = im.crop((150, 100, 2400, 900))
small = small.resize((small.width * 2 // 3, small.height * 2 // 3), Image.LANCZOS)
small.save(pre + "_profil_s.png")
small = im.crop((300, 960, 2300, 1720))
small = small.resize((small.width * 3 // 4, small.height * 3 // 4), Image.LANCZOS)
small.save(pre + "_plan_s.png")
print("ok")
