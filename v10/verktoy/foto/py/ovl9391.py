import sys, json; sys.path.insert(0, '.')
import numpy as np
from PIL import Image, ImageDraw
import common as c, uwlib as U, cands
cam_p = json.load(open(c.W + "/out/cam9391.json"))["ftight"]["p"][:7]
cam = U.Cam(cam_p, 1500, 2000)
im = Image.open(c.FOTO + "/IMG_9391.jpg").convert("RGB"); d = ImageDraw.Draw(im)
def draw_mesh_outline(col, step=4):
    V, F = U.hull_mesh(200, 60)
    rows = np.arange(0, 2000, step, dtype=float)
    lo, hi = U.row_extents(cam, V, F, rows)
    pts = [(lo[i], rows[i]) for i in range(len(rows)) if np.isfinite(lo[i])]
    pts2 = [(hi[i], rows[i]) for i in range(len(rows)) if np.isfinite(hi[i])]
    d.line(pts, fill=col, width=3); d.line(pts2, fill=col, width=3)
    # stations as section curves
    for x in (2000, 3000, 4000, 5000, 6000, 7000, 7600):
        s = np.array(c.C.section(x, 40)); s2 = s[::-1].copy(); s2[:, 0] *= -1
        ss = np.vstack([s2, s])
        X = np.c_[np.full(len(ss), x), ss]
        u, v, z = cam.project(X)
        d.line(list(zip(u, v)), fill=col, width=1)
    # DWL line on hull
    xs = np.linspace(1100, 7800, 60)
    for sg in (1, -1):
        X = np.array([[x, sg * c.C.wl_half_breadth(x), 0.0] for x in xs])
        u, v, z = cam.project(X); d.line(list(zip(u, v)), fill=col, width=1)
draw_mesh_outline((0, 255, 255))
t = json.load(open(c.W + "/out/t9391.json"))
for v, l, r in t["red_outline"]:
    d.ellipse([l - 3, v - 3, l + 3, v + 3], outline=(255, 255, 0)); d.ellipse([r - 3, v - 3, r + 3, v + 3], outline=(255, 255, 0))
im.crop((0, 300, 1500, 1700)).resize((900, 840)).save(c.W + "/img/ovl9391_today.png")
