"""Overlegg for «nye (4).jpeg»: bildet, dagens modell (arbeidstreet) med
hovedkameraet og et kamera med kjolen som anker, og de sporede punktene.

  python ../../../../tools/memcap.py --gb 3 --lock -- python n4_ovl.py [hovedkamera] [kjolkamera]

Ut: v10/rapporter/13nov_nye/n4_overlay.png (utsnitt v 280-770, skalert 1,3 ->
1521 px bredt).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import common as c
import uwlib as U
import geo9374 as G
import n4_cam as K

S = 1.3
BOX = (0, 280, 1170, 770)
IMG = r"C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/nye (4).jpeg"
OUT = c.REPO + "/v10/rapporter/13nov_nye/n4_overlay.png"


def load(tag):
    """Kamera fra n4_cam.json, eller fra n4_fprof.json med 'fprof:<navn>'
    (f laast, f.eks. 'fprof:pin_N_f850')."""
    if tag and tag.startswith("fprof:"):
        import json
        J = json.load(open(c.W + "/out/n4_fprof.json"))
        d = J["out"][tag[6:]]
        q = np.asarray(d["q"], float)
        return K.make_cam(q, d["cm"]), dict(q=q, extra=d["extra"], cmode=d["cm"])
    return K.load(tag)


def main(main_tag=None, keel_tag="pin_K"):
    T = K.T
    cam, d = load(main_tag)
    main_tag = main_tag or K.tags()[0]
    camk, dk = load(keel_tag)
    im = Image.open(IMG).convert("RGB").crop(BOX)
    im = im.resize((int(im.width * S), int(im.height * S)), Image.LANCZOS)
    LEG = 118
    canvas = Image.new("RGB", (im.width, im.height + LEG), (0, 0, 0))
    canvas.paste(im, (0, 0))
    dr = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except OSError:
        font = ImageFont.load_default()

    def P2(u, v):
        return ((u + 0.5 - BOX[0]) * S, (v + 0.5 - BOX[1]) * S)

    def line(u, v, col, w=2, gap=None):
        pts = [P2(a, b) for a, b in zip(u, v) if np.isfinite(a) and np.isfinite(b)]
        if gap is None:
            if len(pts) > 1:
                dr.line(pts, fill=col, width=w)
            return
        for i in range(0, len(pts) - 1, gap):            # stiplet
            seg = pts[i:i + max(gap // 2, 2)]
            if len(seg) > 1:
                dr.line(seg, fill=col, width=w)

    def dot(u, v, col, r=1.6):
        x, y = P2(u, v)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=col)

    VH, FH = K.VH, K.FH
    VK, FK = K.VK, K.FK
    VR, FR = G.rudder_mesh()
    rows = np.arange(300.0, 760.0, 0.5)
    cols = np.arange(0.0, 1170.0, 0.5)

    def silhouette(cm, col, w, gap=None, parts=("hull", "keel", "rud")):
        lo, hi = U.row_extents(cm, VH, FH, rows)
        _, vb = U.row_extents(cm, VH, FH, cols, axis="col")
        a, b = U.row_extents(cm, VH, FH, cols, axis="col")
        if "hull" in parts:
            m = rows > 330
            line(lo[m], rows[m], col, w, gap)
            line(hi[m], rows[m], col, w, gap)
            line(cols, a, col, w, gap)
            line(cols, vb, col, w, gap)
        okb = np.isfinite(vb)

        def below(u, v):
            """True der (u, v) ligger under skrogets nedre silhuett."""
            h = np.interp(u, cols[okb], vb[okb], left=np.nan, right=np.nan)
            return np.isfinite(u) & np.isfinite(v) & (v > h - 0.5)
        if "keel" in parts:
            lk, hk = U.row_extents(cm, VK, FK, rows)
            _, bk = U.row_extents(cm, VK, FK, cols, axis="col")
            m = below(lk, rows)
            line(lk[m], rows[m], col, w, gap)
            m = below(hk, rows)
            line(hk[m], rows[m], col, w, gap)
            m = below(cols, bk)
            line(cols[m], bk[m], col, w, gap)
        if "rud" in parts:
            lr, hr = U.row_extents(cm, VR, FR, rows)
            _, br = U.row_extents(cm, VR, FR, cols, axis="col")
            m = below(lr, rows)
            line(lr[m], rows[m], col, w, gap)
            m = below(hr, rows)
            line(hr[m], rows[m], col, w, gap)
            m = below(cols, br)
            line(cols[m], br[m], col, w, gap)

    CY, YE, GR, MA, WH, RE = (0, 230, 255), (255, 215, 0), (120, 255, 120), (255, 80, 255), (255, 255, 255), (255, 40, 40)
    silhouette(camk, GR, 1, gap=6)
    silhouette(cam, CY, 2)
    # fenderlisten og bunnstoffkanten i modellen (hovedkameraet)
    u, v, _ = cam.project(K.STRAKE3)
    line(u, v, RE, 1)
    zr = 38.0
    X = G.zline3(lambda x: zr, 1200.0, 7800.0, 200)
    u, v, _ = cam.project(X)
    line(u, v, MA, 1)
    if "bt_dz_red" in d["extra"]:
        dz, k = d["extra"]["bt_dz_red"], d["extra"]["bt_k"]
        X = G.zline3(lambda x: zr + dz + k * (x - 4000.0) / 1000.0, 2000.0, 7800.0, 200)
        u, v, _ = cam.project(X)
        line(u, v, MA, 1, gap=4)
    # vinduets ender: modell (roede ringer) og bilde (hvite kryss)
    u, v, _ = cam.project(G.window_ends())
    for a, b in zip(u, v):
        x, y = P2(a, b)
        dr.ellipse([x - 5, y - 5, x + 5, y + 5], outline=RE, width=2)
    for key in ("fwd_end", "aft_end"):
        x, y = P2(*T["window"][key])
        dr.line([x - 5, y - 5, x + 5, y + 5], fill=WH, width=2)
        dr.line([x - 5, y + 5, x + 5, y - 5], fill=WH, width=2)
    # sporede punkter (hvite)
    A = lambda k: np.asarray(T[k], float)
    for uu, vv in np.r_[A("bottom"), A("bottom_dark")][::2]:
        if uu > 560 or vv < 514:
            continue
        dot(uu, vv, WH)
    for vv, uu, _ in A("front")[::2]:
        dot(uu, vv, WH)
    for vv, uu in np.r_[A("crease"), A("stem_hi"), A("stem_wl")][::3]:
        dot(uu, vv, WH, 1.2)
    for vv, uu in np.r_[A("keel_le"), A("keel_te")][::2]:
        dot(uu, vv, WH)
    for uu, vv in A("keel_bot")[::2]:
        dot(uu, vv, WH)
    for vv, a, b in A("rudder")[::2]:
        dot(a, vv, WH); dot(b, vv, WH)
    for uu, vv in A("rudder_bot")[::2]:
        dot(uu, vv, WH)
    bt = A("boottop")
    for uu, _, _, vv in bt[::6]:
        if np.isfinite(vv):
            dot(uu, vv, WH, 1.0)
    # forklaring
    y0 = im.height + 6
    q = d["q"]
    lines = [
        ("«nye (4).jpeg» mot dagens V10-modell (arbeidstreet, trinn 5). Hvite prikker = sporet i bildet "
         "(bunnens og forfotens omriss, stevn, kjol, ror, bunnstoffkant).", WH),
        ("Cyan = modellens omriss (skrog, kjol, ror), hullkamera %s (f %.0f px laast; anker: liste, stevn z 300-750, "
         "hekkens hjoerne, bunnstoffkantens form; IKKE kjolen)." % (main_tag.replace("fprof:", ""), q[6]), CY),
        ("Stiplet groenn = %s: samme ankre med radial fortegning k1 %.2f. Forkastet: stevnen passer, men kjolens "
         "flate bunn blir skjev (25 px rms)." % (keel_tag.replace("fprof:", ""), dk["extra"].get("k1", 0.0)), GR),
        ("Roed = fenderlisten i modellen. Magenta = bunnstoffkant z 38 (IMG_9370), stiplet = tilpasset hoeyde i "
         "dette bildet. Roede ringer/hvite kryss = vinduets ender modell/bilde.", MA),
        ("Kilen bak stevnen og den roede kilen foran kjolen er en annen baat bak denne (samme fargeskjema); "
         "stoettene skjuler omrisset ved u 352-398 og 446-560.", WH),
    ]
    for i, (txt, col) in enumerate(lines):
        dr.text((10, y0 + 22 * i), txt, fill=col, font=font)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    canvas.save(OUT)
    print("skrev", OUT, canvas.size)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if a else None, a[1] if len(a) > 1 else "pin_K")
