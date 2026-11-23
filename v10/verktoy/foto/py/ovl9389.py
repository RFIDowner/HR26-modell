"""Overleggsbilde for IMG_9389 (forkroppen): bildet, sporet omriss (hvite
prikker), modellens omriss med hovedkameraet (cyan: hele modellen,
export/stl/01_skrog.stl = commit 0976477), kjolen (magenta) og, om den
finnes, arbeidskopiens forkropp (gul; lages med HR26_REF=work --dump).

  HR26_REF=work python ovl9389.py --dump      # gul linje (arbeidskopien)
  python ovl9389.py                           # bildet
"""
import json
import os
import sys
import tempfile

import numpy as np

import head9389  # noqa: F401
import common as c
import uwlib as U
import geo9389 as G

K = 0.5                                   # 2000 -> 1000 px
OUT = os.path.join(c.REPO, "v10", "rapporter", "13nov_kveld", "forkropp_9389.png")
DUMP = os.path.join(tempfile.gettempdir(), "hr26_ovl9389_%s.json")
CJ = json.load(open(c.W + "/out/cam9389.json"))
CAM = U.Cam(CJ["p"], 2000, 1500)
T = json.load(open(c.W + "/out/t9389_forkropp.json"))


def outline(V, F, step=2.0, x_max=5000.0):
    Vf = V[F]
    Fk = F[(Vf[:, :, 0].min(1) < x_max) & (Vf[:, :, 2].min(1) < 400.0)]
    cols = np.arange(1000.0, 2000.0, step)
    _, hi = U.row_extents(CAM, V, Fk, cols, axis="col")
    rows = np.arange(300.0, 470.0, step)
    _, hu = U.row_extents(CAM, V, Fk, rows)
    pts = [(u, v) for u, v in zip(cols, hi) if np.isfinite(v)] + [(u, v) for v, u in zip(rows, hu) if np.isfinite(u)]
    return np.array(pts)


if __name__ == "__main__":
    import photos
    V, F = photos.mesh()
    if "--dump" in sys.argv:
        c.save_json(dict(ref=head9389.REF, pts=outline(V, F)), DUMP % head9389.REF)
        sys.exit(0)
    from PIL import Image, ImageDraw, ImageFont
    from scipy import ndimage as ndi
    import e9389 as E
    import stl9389
    im = Image.open(c.FOTO + "/IMG_9389.jpg").convert("RGB").resize((1000, 750), Image.LANCZOS)
    a = np.asarray(im).copy()
    # hele modellen (STL) - cyan omriss
    img, fid, depth, cam = stl9389.render(CJ["p"], K)
    m = fid >= 0
    e = m & ~ndi.binary_erosion(m)
    a[ndi.binary_dilation(e)] = (0, 230, 255)
    im = Image.fromarray(a)
    d = ImageDraw.Draw(im)

    def dots(P, col, r=1.6):
        for u, v in P:
            if np.isfinite(u) and np.isfinite(v):
                d.ellipse([u * K - r, v * K - r, u * K + r, v * K + r], fill=col)

    def line(P, col, w=2):
        P = [(u * K, v * K) for u, v in P if np.isfinite(u) and np.isfinite(v)]
        if len(P) > 1:
            d.line(P, fill=col, width=w)

    # kjolen (magenta, fra kjolnettet)
    VK, FK = G.keel_mesh()
    rows = np.arange(640.0, 960.0, 2.0)
    lo, hi = U.row_extents(CAM, VK, FK, rows)
    line([(x, r) for x, r in zip(lo, rows)], (255, 0, 255), 1)
    line([(x, r) for x, r in zip(hi, rows)], (255, 0, 255), 1)
    cols = np.arange(600.0, 1000.0, 2.0)
    _, hv = U.row_extents(CAM, VK, FK, cols, axis="col")
    line([(u, v) for u, v in zip(cols, hv)], (255, 0, 255), 1)
    # arbeidskopien (gul), om den er dumpet
    if os.path.exists(DUMP % "work"):
        W = np.asarray(json.load(open(DUMP % "work"))["pts"], float)
        dots(W, (255, 220, 0), 1.0)
    # dagens analytiske skrog (commit 0976477) i cyan prikker langs forkroppen
    dots(outline(V, F, 4.0), (0, 230, 255), 1.0)
    # sporet: omriss (hvitt), stripens nedre kant (groenn, tynn)
    bot = np.asarray(T["bottom"], float)
    fr = np.asarray(T["front"], float)[:, ::-1]
    dots(bot[::2], (255, 255, 255), 1.8)
    dots(fr[::2], (255, 255, 255), 1.8)
    dots(np.asarray(T["bt_red"], float)[::3], (120, 255, 120), 0.9)
    # x-merker langs omrisset (fra dagens modell)
    Xb, Xf = E.outline_points(V, F)
    for xm in (1000, 1500, 2000, 2500):
        i = int(np.nanargmin(np.abs(Xb[:, 0] - xm)))
        if abs(Xb[i, 0] - xm) < 60:
            u, v = E.BOT[i]
            d.line([(u * K, v * K + 4), (u * K, v * K + 16)], fill=(255, 255, 255), width=1)
            d.text((u * K - 14, v * K + 17), "x %d" % xm, fill=(255, 255, 255))
    rb, rf = E.parts(V, F)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
    except OSError:
        font = None
    txt = ["IMG_9389 - kamera fra fenderlist, kjol og stripen (hele lengden), f %.0f px" % CJ["p"][6],
           "hvitt: sporet omriss under vann   cyan: dagens modell (STL / analytisk)   magenta: kjolen",
           "gult: arbeidskopien (trinn 5 underveis)   groent: stripens nedre kant (sporet)",
           "commit 0976477: forfot %+.0f px, bunn %+.0f px i snitt (+ = modellen utenfor bildets omriss)"
           % (rf.mean(), rb.mean())]
    for i, t in enumerate(txt):
        d.text((8, 6 + 18 * i), t, fill=(0, 0, 0), font=font)
        d.text((7, 5 + 18 * i), t, fill=(255, 255, 255), font=font)
    im.save(OUT)
    print("lagret", OUT, im.size)
