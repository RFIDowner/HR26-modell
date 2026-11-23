"""IMG_9526 (foto av et gammelt papirbilde; baaten flyter, sett akterfra litt
fra babord, kamera ca. 0,5 m over vannet). 13.11.2026, akter-maaleren.

BILDET VISER ET BARN: ingenting fra bildet skrives i repoet. Kontrollbildet
gaar til C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/analyse/.

Papiret er haandholdt og kan vaere boeyd, saa et fullt kamera loeses ikke.
Her brukes en enkel, begrenset sammenligning paa akterspeilsflaten (nesten
rett forfra): punktene er lest av paa et hoeypassfiltrert bilde (1/4 skala,
+-10 px der = +-40 px her) og paa 2x-utsnitt.
  * vannrett skala fra akterspeilhjoernene like under listen (halvbredde 788)
  * loddrett skala antas lik (flaten ses nesten rett forfra; feil fra
    skraavinkel og papirboeying: ca. +-8 %)
  * hoeyden regnes fra listens hjoerner (z 804)

Kjoeres fra denne mappa:  python ../../../../tools/memcap.py --gb 3 -- python n9526_meas.py
"""
import json

import numpy as np

import common as c
import n1_geo as N

SRC = r"C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/IMG_9526.jpeg"
OUT = r"C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/analyse/n9526_kontroll.png"

# hjoernelinjene (lys/skygge-grensen mellom akterspeilet og laaringene), (x, y) i bildet
KN_L = [(1000, 1800), (1060, 2200), (1220, 2480), (1280, 2550), (1460, 2660), (1620, 2700)]
KN_R = [(3200, 1820), (3160, 2220), (2950, 2550), (3020, 2520), (2860, 2660), (2740, 2700)]
STRAKE_CORNER_Y = 1760.0           # listens senter ved hjoernene (bildets y), +-25
STRIPE_TOP_Y = 2700.0              # vannlinjestripens blaa overkant paa akterspeilet, +-10
CREAM_Y = 2795.0                   # den hvite linja / overgangen til roedt, +-8
RED_VISIBLE_TO_Y = 2870.0          # roedt synlig ned til papirkanten (vannet er lavere)


def interp_x(pts, y):
    p = np.array(sorted(pts, key=lambda q: q[1]), float)
    return float(np.interp(y, p[:, 1], p[:, 0]))


if __name__ == "__main__":
    yt = N.strake_corner()[1]                      # 788
    w_px = interp_x(KN_R, 1830.0) - interp_x(KN_L, 1830.0)
    s = 2.0 * yt / w_px                            # mm/px
    res = {"mm_per_px": s, "rows": []}
    print(f"skala {s:.3f} mm/px (hjoernene under listen {w_px:.0f} px = {2 * yt:.0f} mm)")
    for y in (2200.0, 2400.0, 2550.0, 2660.0, 2700.0):
        z = 804.0 - (y - STRAKE_CORNER_Y) * s
        hw = 0.5 * (interp_x(KN_R, y) - interp_x(KN_L, y)) * s
        k = N.corner_y(z)
        ym = k[1] if k else 0.0
        res["rows"].append(dict(y_img=y, z=z, y_photo=hw, y_model=ym))
        print(f"  bilde-y {y:5.0f}: z {z:5.0f} (+-{0.08 * (y - STRAKE_CORNER_Y) * s + 25 * s:.0f})  halvbredde foto "
              f"{hw:4.0f}  modell {ym:4.0f}  diff {hw - ym:+4.0f} mm")
    zs = {k: 804.0 - (v - STRAKE_CORNER_Y) * s for k, v in
          (("stripe_top", STRIPE_TOP_Y), ("cream", CREAM_Y), ("red_visible_to", RED_VISIBLE_TO_Y))}
    for k, v in zs.items():
        print(f"  {k}: z {v:.0f} mm (+-{0.08 * (804 - v) + 25 * s:.0f})")
    res["z"] = zs
    c.save_json(res, c.W + "/out/n9526_meas.json")
    from PIL import Image, ImageDraw
    im = Image.open(SRC).convert("RGB")
    d = ImageDraw.Draw(im)
    for pts, col in ((KN_L, (255, 140, 0)), (KN_R, (255, 140, 0))):
        for x, y in pts:
            d.ellipse([x - 14, y - 14, x + 14, y + 14], outline=col, width=5)
    for y, col in ((STRAKE_CORNER_Y, (255, 230, 0)), (STRIPE_TOP_Y, (0, 255, 0)), (CREAM_Y, (255, 255, 255)),
                   (RED_VISIBLE_TO_Y, (255, 0, 0))):
        d.line([(900, y), (3300, y)], fill=col, width=4)
    im.resize((im.width // 2, im.height // 2)).save(OUT)
    print(OUT)
