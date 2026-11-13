"""Overlegg for IMG_9395: bildet, sporet omriss (hvite prikker), dagens modell (cyan), kjol og ror (gul),
stripens nedre kant (hvite prikker) mot modellens linje z = BT_Z (magenta), modellens senterlinje (oransje,
stiplet) mot roedt/graatt-grensen (hvite prikker, smaa). Skriver v10/rapporter/13nov_kveld/forkropp_9395.png.

Kjoeres fra denne mappa: python ../../../../tools/memcap.py --gb 3 -- python ovl9395.py
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import common as c
import e9395 as E
import geo9395 as G
import photos
import uwlib as U

OUT = c.REPO + "/v10/rapporter/13nov_kveld/forkropp_9395.png"
X0, Y0, X1, Y1 = 780, 270, 1780, 1290
CYAN, YEL, MAG, ORA, WHITE = (0, 235, 255), (255, 225, 0), (255, 60, 220), (255, 150, 30), (255, 255, 255)


def font(sz):
    for f in ("C:/Windows/Fonts/arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def outline_pts(cam, V, F, r0=250, r1=1300, c0=820, c1=1820):
    rows = np.arange(r0, r1, 1.0)
    lo, hi = U.row_extents(cam, V, F, rows)
    cols = np.arange(c0, c1, 1.0)
    clo, chi = U.row_extents(cam, V, F, cols, axis="col")
    P = []
    for r, a, b in zip(rows, lo, hi):
        if np.isfinite(a):
            P += [(a, r), (b, r)]
    for cc, a, b in zip(cols, clo, chi):
        if np.isfinite(a):
            P += [(cc, a), (cc, b)]
    return P


def main():
    cam = E.CAM
    im = Image.open(c.FOTO + "/IMG_9395.jpg").convert("RGB")
    d = ImageDraw.Draw(im)
    V, F = photos.mesh()
    VK, FK = G.keel_mesh()
    VR, FR = G.rudder_mesh()

    def dot(u, v, col, r=1.6):
        d.ellipse([u - r, v - r, u + r, v + r], fill=col)

    for (u, v) in outline_pts(cam, V, F):
        d.point((u, v), fill=CYAN)
        d.point((u + 0.6, v + 0.6), fill=CYAN)
    for VV, FF in ((VK, FK), (VR, FR)):
        for (u, v) in outline_pts(cam, VV, FF, 1000, 1300, 1250, 1720):
            d.point((u, v), fill=YEL)
    # modellens senterlinje (kjol/stevn) forut for kjolen
    xs = np.linspace(500, 3380, 200)
    u, v, _ = cam.project(G.centreline(xs))
    for i in range(0, len(u) - 1, 2):
        d.line([(u[i], v[i]), (u[i + 1], v[i + 1])], fill=ORA, width=2)
    # modellens linje z = BT_Z paa babord side
    X = E.zline(V, F, E.BT_Z, xmax=5600)
    u, v, _ = cam.project(X)
    o = np.argsort(u)
    d.line(list(zip(u[o], v[o])), fill=MAG, width=2)
    for (uu, vv) in E.BT[::3]:
        dot(uu, vv, WHITE, 1.2)
    for (vv, uu) in np.asarray(E._J["red_grey_rows"])[::3]:
        dot(uu, vv, WHITE, 1.0)
    # sporet omriss
    for (vv, uu) in E.BOW[::3]:
        dot(uu, vv, (200, 200, 200), 1.8)
    for (vv, uu) in E.ROWS[::3]:
        dot(uu, vv, WHITE, 2.0)
    for (uu, vv) in E.COLS[::3]:
        dot(uu, vv, WHITE, 2.0)
    for (uu, vv) in E.COLS_KR[::3]:
        dot(uu, vv, (200, 200, 200), 1.8)
    # avvik per omraade (px, + = modellen utenfor bildets omriss)
    s = E.summary(V, F, verbose=False)["regions"]
    ft = font(15)
    notes = [("baug over vann rad 545-705 (ikke i resid)", (790, 600), "baug over vann"),
             ("forfot rad 705-850", (850, 760), "forfot"),
             ("styrbord bunn rad 850-945", (905, 905), "styrb. bunn z~-100"),
             ("bunn u 1180-1215", (1030, 1075), "slag x 3300-3700"),
             ("bunn foran kjolen u 1252-1299", (1130, 1110), "bunn x 3700-3900"),
             ("kjolrot u 1300-1335 (ikke i resid)", (1230, 1140), "kjolrot")]
    for key, (uu, vv), lab in notes:
        if key in s:
            m = s[key]
            txt = "%s: %+.0f px (%+.0f mm)" % (lab, m["mean"], m["mean"] * m["mm_per_px"])
            tw = d.textlength(txt, font=ft)
            d.rectangle([uu - 3, vv - 2, uu + tw + 3, vv + 18], fill=(0, 0, 0))
            d.text((uu, vv), txt, fill=CYAN, font=ft)
    crop = im.crop((X0, Y0, X1, Y1))
    W = crop.size[0]
    if W > 1000:
        k = 1000 / W
        crop = crop.resize((1000, round(crop.size[1] * k)), Image.LANCZOS)
    # forklaring
    leg = Image.new("RGB", (crop.size[0], 74), (250, 250, 250))
    dl = ImageDraw.Draw(leg)
    f = font(14)
    items = [(WHITE, "sporet: omriss (graa = ikke i resid), stripens nedre kant, rodt/graatt"),
             (CYAN, "dagens modell, omriss (analytisk skrog)"), (YEL, "modellens kjol og ror"),
             (MAG, "modellens linje z = %.0f (stripens nedre kant)" % E.BT_Z), (ORA, "modellens senterlinje (kjol/stevn)")]
    x, y = 8, 6
    for col, txt in items:
        dl.rectangle([x, y + 3, x + 14, y + 13], fill=col if col != WHITE else (120, 120, 120), outline=(0, 0, 0))
        dl.text((x + 20, y), txt, fill=(20, 20, 20), font=f)
        y += 22
        if y > 50:
            x, y = crop.size[0] // 2 + 10, 6
    out = Image.new("RGB", (crop.size[0], crop.size[1] + leg.size[1]), (255, 255, 255))
    out.paste(leg, (0, 0))
    out.paste(crop, (0, leg.size[1]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT)
    print("skrev", OUT, out.size)


if __name__ == "__main__":
    main()
