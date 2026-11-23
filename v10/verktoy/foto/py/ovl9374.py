"""Overlegg for IMG_9374: bildet, sporet omriss (hvite prikker), dagens modells
omriss (cyan, analytisk skrog + kjol), kjolens omriss (gult) og - med --diag -
kamera-trekkene (fenderlist, vindu, stripe, ror).

  python ../../../../tools/memcap.py --gb 3 -- python ovl9374.py [--diag] [ut.png]

Standard ut: v10/rapporter/13nov_kveld/forkropp_9374.png (bredde 761 px x 1,3
= 990 px, under 1000 px).
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

import common as c
import uwlib as U
import geo9374 as G
import e9374 as E

S = 1.3


def main(out=None, diag=False):
    G.use_model()           # dagens modell = commit G.MODEL_REV (det eieren saa), ikke trinn 5 underveis
    cam = E.CAM
    im = Image.open(c.FOTO + "/IMG_9374.jpg").convert("RGB")
    W0, H0 = im.size
    im = im.resize((int(W0 * S), int(H0 * S)), Image.LANCZOS)
    d = ImageDraw.Draw(im)

    def pt(u, v, col, r=1.3):
        x, y = (u + 0.5) * S, (v + 0.5) * S
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    def line(uv, col, w=1):
        uv = [((a + 0.5) * S, (b + 0.5) * S) for a, b in uv if np.isfinite(a) and np.isfinite(b)]
        if len(uv) > 1:
            d.line(uv, fill=col, width=w)

    V, F = U.hull_mesh(220, 60)
    VK, FK = G.keel_mesh()
    # modellens omriss: per rad (venstre/hoeyre kant) og per kolonne (nedre kant)
    rows = np.arange(100.0, 440.0, 0.5)
    lo_h, hi_h = U.row_extents(cam, V, F, rows)
    lo_k, hi_k = U.row_extents(cam, VK, FK, rows)
    lo = np.fmin(lo_h, lo_k)
    cols = np.arange(0.0, 761.0, 0.5)
    _, vb_h = U.row_extents(cam, V, F, cols, axis="col")
    _, vb_k = U.row_extents(cam, VK, FK, cols, axis="col")
    vb = np.fmax(vb_h, vb_k)
    cyan = (0, 235, 255)
    m = np.isfinite(lo) & (rows > 240)
    line(list(zip(lo[m], rows[m])), cyan, 2)
    m = np.isfinite(vb) & (cols < 700)
    line(list(zip(cols[m], vb[m])), cyan, 2)
    # kjolens omriss i senterplanet (tynn gul)
    ko = G.keel_outline_xz()
    u, v, _ = cam.project(np.c_[ko[:, 0], np.full(len(ko), -120.0), ko[:, 1]])
    line(list(zip(u, v)), (255, 220, 0), 1)
    if diag:
        import cam9374 as K
        u, v, _ = cam.project(K.STRAKE3)
        line(list(zip(u, v)), (255, 255, 0), 1)
        u, v, _ = cam.project(K.STEM3)
        line(list(zip(u, v)), (0, 255, 0), 1)
        u, v, _ = cam.project(K.WIN3)
        for a, b in zip(u, v):
            pt(a, b, (255, 0, 0), 3)
        for a, b in K.OBS["window"]:
            pt(a, b, (255, 255, 255), 2)
        VR, FR = G.rudder_mesh()
        rr = np.arange(250.0, 440.0, 1.0)
        a, b = U.row_extents(cam, VR, FR, rr)
        line(list(zip(a, rr)), (255, 128, 0), 1)
        line(list(zip(b, rr)), (255, 128, 0), 1)
        J = json.load(open(c.W + "/out/cam9374.json"))
        K.CMODE["m"] = E._CD["cmode"]
        BT, BR = K.bt_lines(J["bt_dz_top"], J["bt_dz_red"], J["bt_slope_per_m"])
        u, v, _ = cam.project(BT); line(list(zip(u, v)), (255, 0, 255), 1)
        u, v, _ = cam.project(BR); line(list(zip(u, v)), (255, 0, 255), 1)
        st = np.asarray(K.OBS["strake"])
        for a, b in st[::3]:
            pt(a, b, (255, 255, 255), 0.8)
    # sporet omriss (hvite prikker)
    T = json.load(open(c.W + "/out/t9374_forkropp.json"))
    for vv, uu in np.asarray(T["front"], float):
        pt(uu, vv, (255, 255, 255))
    for uu, vv in np.asarray(T["bottom"], float):
        pt(uu, vv, (255, 255, 255))
    for uu, vv in np.asarray(T["bt_red"], float)[::2]:
        pt(uu, vv, (255, 255, 255), 0.9)
    # forklaring
    d.rectangle([6, int(H0 * S) - 64, 520, int(H0 * S) - 6], fill=(0, 0, 0))
    d.text((12, int(H0 * S) - 60), "IMG_9374: hvite prikker = sporet omriss under vann foran kjolen", fill=(255, 255, 255))
    d.text((12, int(H0 * S) - 44), "          + nedre kant av den lyse stripen (overgang til roedt)", fill=(255, 255, 255))
    d.text((12, int(H0 * S) - 28), "cyan = modellen %s (skrog + kjol), gult = kjolens omriss, kamera %s"
           % (G.MODEL_REV, E._CJ["main"]), fill=cyan)
    out = out or (c.REPO + "/v10/rapporter/13nov_kveld/forkropp_9374.png")
    im.save(out)
    print("skrev", out, im.size)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else None, diag="--diag" in sys.argv)
