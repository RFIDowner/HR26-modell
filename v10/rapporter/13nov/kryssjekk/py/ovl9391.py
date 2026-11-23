"""IMG_9391 overlay: photo red-outline trace (white), the 448-5 dash-dot level line projected at z=-300 (yellow),
and model outlines for V1 (cyan) and HEAD (magenta) with the zc5 camera."""
import sys, json, importlib
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from hr26 import params as P, curves as C
UPY = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/undervann/py"
KK = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/"
sys.path.insert(1, UPY)
import numpy as np
from PIL import Image, ImageDraw
import common as c, uwlib as U
import photos as PH
cam = U.Cam(json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"][:7], 1500, 2000)
im = Image.open(c.FOTO + "/IMG_9391.jpg").convert("RGB")
d = ImageDraw.Draw(im)
ro = np.array(json.load(open(c.W + "/out/t9391.json"))["red_outline"])
for r, uL, uR in ro:
    d.point([(uL, r), (uR, r)], fill=(255, 255, 255))
    d.ellipse([uL - 1.5, r - 1.5, uL + 1.5, r + 1.5], outline=(255, 255, 255))
    d.ellipse([uR - 1.5, r - 1.5, uR + 1.5, r + 1.5], outline=(255, 255, 255))
rows = np.arange(700.0, 1010.0, 2.0)
def outline(col):
    V, F = PH.mesh()
    lo, hi = U.row_extents(cam, V, F, rows)
    for r, a, b in zip(rows, lo, hi):
        if np.isfinite(a):
            d.point([(a, r), (b, r)], fill=col); d.point([(a + 1, r), (b - 1, r)], fill=col)
outline((0, 255, 255))                          # V1 (stage s4)
s0p = {}; exec(open(sys.argv[2] + "/hr26/params.py", encoding="utf-8").read(), s0p)
for k in ("SECTION_N", "SECTION_DEADRISE", "CANOE_BOTTOM_HIDDEN"):
    setattr(P, k, s0p[k])
P.DEADWOOD_H = [(0.0, 0.0), (8000.0, 0.0)]; P.DEADWOOD_W = 180.0
C = importlib.reload(sys.modules["hr26.curves"]); c.C = C; U.c.C = C
outline((255, 0, 255))                          # HEAD
tr = json.load(open(KK + "out/dashdot_trace.json"))
for side, sgn in (("stb", 1), ("port", -1)):
    a = np.array(tr[side]); a = a[(a[:, 0] >= 3000) & (a[:, 0] <= 5300)]
    X = np.c_[a[:, 0], sgn * np.abs(a[:, 1]), np.full(len(a), -300.0)]
    u, v, _ = cam.project(X)
    for ui, vi in zip(u, v):
        d.ellipse([ui - 3, vi - 3, ui + 3, vi + 3], outline=(255, 230, 0), width=2)
im = im.crop((0, 560, 1500, 1160))
im.save(sys.argv[3]); print(im.size)
