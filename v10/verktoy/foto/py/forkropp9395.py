"""Bygger out/t9395_forkropp.json: forkroppens omriss og vannlinjestripen i IMG_9395, klart for e9395.py.

Leser out/t9395_raw.json (sporingen, t9395.py) og out/cam9395.json (kameraet). Kjolen og roret
(ikke i det analytiske nettet) projiseres med kameraet, og rader/kolonner der de kunne danne eller
skjule omrisset merkes som utelatt. Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python forkropp9395.py
"""
import json

import numpy as np

import common as c
import geo9395 as G
import uwlib as U

T = json.load(open(c.W + "/out/t9395_raw.json"))
CAMJ = json.load(open(c.W + "/out/cam9395.json"))
CAM = U.Cam(CAMJ["p"], CAMJ["W"], CAMJ["H"])
STRIPE_DZ = float(CAMJ["stripe_dz"]["red"]["dz"])          # stripens forskyvning maalt paa baugen


def a(k):
    return np.asarray(T[k], float)


DESC = {
    "_photo": "docs/foto/IMG_9395.jpg, 2400 x 1800 px, u mot hoeyre, v nedover. Baaten henger i travelliften, "
              "sett forfra-nedenfra fra babord side (kamera ca. 3,8 m foran stevnen, 2,9 m ut til babord, "
              "1,6 m under DWL; se out/cam9395.json).",
    "outline_rows": "[v, u] per bilderad: venstre/nedre omriss av forkroppen mot himmelen (det som ligger lengst "
                    "til venstre i raden). Rad 545-705: baugen over vann (z ca. 650 -> 300, styrbord side naer "
                    "stevnen); rad 705-945: forfoten og styrbord bunn under vann. Model: min u av nettet i raden.",
    "outline_cols": "[u, v] per bildekolonne: nedre omriss av forkroppen mot himmelen (det som ligger lavest i "
                    "kolonnen), fra forfoten (u 1121) til like foran kjolens forkant (u 1335). u 1216-1252 mangler "
                    "(loefteauet og sjakkelen henger der). Model: max v av nettet i kolonnen.",
    "outline_rows_keep / outline_cols_keep": "1 = brukes i e9395.resid, 0 = utelatt (kjol/ror kan danne eller "
                    "skjule omrisset, eller rad 545-705 over vann).",
    "strap_cols": "[u0, u1]: her ligger loftestroppen langs omrisset (u 1100-1176); omrisset kan ligge 3-6 px "
                  "utenfor skroget (stroppens tykkelse).",
    "bt_lower": "[u, v]: vannlinjestripens nedre kant (kremlinjen -> roedt) paa babord side, u 1047-1680 "
                "(stroppen u 1515-1600 utelatt). IMG_9370 gir z +38 for denne kanten; i dette bildet ligger "
                "stripen hoeyere (se bt_z).",
    "bt_upper": "[u, v]: stripens overkant (hvit -> blaa), samme kolonner. IMG_9370: z 146 (x 1000) til 125 (x 5500).",
    "bt_z": "Hoeyden e9395.resid_bt bruker for nedre kant: 38 + stripe_dz, der stripe_dz er maalt paa de forreste "
            "60 px av stripen (x ca. 850-1150, smal baug) med kameraet. Usikker med ca. +-30 mm.",
    "red_grey_rows": "[v, u]: grensen mellom roedt (babord bunn, sett rett paa) og graatt (flater sett paa skraa "
                     "som speiler himmelen) paa forfoten, per rad. Trolig kjollinjen/senterlinjen (V-en) eller "
                     "der bunnen vender seg bort; brukes bare som kontroll (e9395.summary).",
    "red_grey_cols": "[u, v]: samme grense per kolonne (u 1130-1210).",
    "bow_left_above_wl": "[v, u]: venstre omriss rad 545-705 (baugen over vann), kopi av en del av outline_rows.",
}


def keel_rudder_masks(rows, cols, out_rows, out_cols, margin=4.0):
    VK, FK = G.keel_mesh()
    VR, FR = G.rudder_mesh()
    keep_r = np.ones(len(rows), bool)
    keep_c = np.ones(len(cols), bool)
    for V, F in ((VK, FK), (VR, FR)):
        lo, hi = U.row_extents(CAM, V, F, rows)
        # kjolen i raden og til venstre for (eller naer) omrisset -> utelat
        keep_r &= ~(np.isfinite(lo) & (lo < out_rows + margin))
        lo, hi = U.row_extents(CAM, V, F, cols, axis="col")
        keep_c &= ~(np.isfinite(hi) & (hi > out_cols - margin))
    return keep_r, keep_c


if __name__ == "__main__":
    L = a("left")
    rows = L[(L[:, 0] >= 545) & (L[:, 0] <= 945)]
    B = a("bottom")
    cols = B[(B[:, 0] >= 1121) & (B[:, 0] <= 1335)]
    kr, kc = keel_rudder_masks(rows[:, 0], cols[:, 0], rows[:, 1], cols[:, 1])
    kr &= rows[:, 0] >= 705
    print("rows kept %d/%d, cols kept %d/%d" % (kr.sum(), len(kr), kc.sum(), len(kc)))
    if (~kc).any():
        print("cols dropped:", cols[~kc, 0].min(), cols[~kc, 0].max())
    sp = a("stripe")
    oks = ~((sp[:, 0] >= 1515) & (sp[:, 0] <= 1600)) & (sp[:, 0] <= 1680)
    rgr = a("red_inner_rows")
    rgr = rgr[(rgr[:, 0] >= 750) & (rgr[:, 0] <= 980)]
    rgc = a("red_inner_cols")
    rgc = rgc[(rgc[:, 0] >= 1130) & (rgc[:, 0] <= 1210)]
    out = dict(DESC=DESC, outline_rows=rows, outline_rows_keep=kr.astype(int),
               outline_cols=cols, outline_cols_keep=kc.astype(int), strap_cols=[1100, 1176],
               bt_lower=sp[oks][:, [0, 3]], bt_upper=sp[oks][:, [0, 1]],
               bt_z=G.Z_RED + STRIPE_DZ, stripe_dz=CAMJ["stripe_dz"],
               red_grey_rows=rgr, red_grey_cols=rgc,
               bow_left_above_wl=rows[rows[:, 0] < 705], camera=CAMJ["p"])
    c.save_json(out, c.W + "/out/t9395_forkropp.json")
    print("bt_z", out["bt_z"])
