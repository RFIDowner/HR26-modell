"""Forkroppen under vann i IMG_9374: utvalg -> ../out/t9374_forkropp.json.

Trenger ../out/t9374_raw.json, ../out/t9374_cam.json (t9374.py) og
../out/cam9374.json (cam9374.py).

Omrisset av skroget fra stevnen (under z ~ +300) ned rundt forfoten og
akterover langs bunnen til der kjolen (modellens kjol med hulkil, sett med
hovedkameraet) begynner aa danne omrisset:
  front   per bilderad: venstre kant av skroget (stevn/forfot), der kanten er
          brattere enn 45 grader i bildet
  bottom  per bildekolonne: nederste kant av det roede, der kanten er slakere
          enn 45 grader
  bt_red  nedre kant av den lyse stripen (overgang til roedt) forut for x 3 800
  bt_top  blaa overkant forut, samme utvalg (bare til orientering)
Luket bort: fremre stropp (krysser bunnen ved u ~ 400-420 og stripen ved
u ~ 465-505), alt der kjolen ville danne omrisset (+ margin), og punkter som
avviker fra en glidende median.
Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python fk9374.py
"""
import json

import numpy as np

import common as c
import uwlib as U
import geo9374 as G

G.use_model()            # modellen fra commit G.MODEL_REV (foer trinn 5), se geo9374.use_model
P, C = c.P, c.C
CAM, CD = G.load_cam()
CJ = json.load(open(c.W + "/out/cam9374.json"))
DZT, DZR, KS = CJ["bt_dz_top"], CJ["bt_dz_red"], CJ["bt_slope_per_m"]
KEEL_MARGIN = 8.0        # px foran der kjolen begynner aa danne omrisset


def z_red(x):
    return 38.0 + DZR + KS * (np.asarray(x, float) - 4000.0) / 1000.0


def z_top(x):
    return G.bt_top_z(np.asarray(x, float)) + DZT + KS * (np.asarray(x, float) - 4000.0) / 1000.0


def robust_keep(a, b, win=6, tol=2.5):
    keep = np.ones(len(a), bool)
    for i in range(len(a)):
        lo, hi = max(i - win, 0), min(i + win + 1, len(a))
        if abs(b[i] - np.median(b[lo:hi])) > tol:
            keep[i] = False
    return keep


def silhouette_pt(cam, V, F, obs, axis):
    """Modellens silhuettpunkt for hver observasjon: toppunktet som gir
    ytterpunktet i kolonnen (axis='col', stoerst v) eller raden ('row', minst
    u). Gir [x, y, z, mm per px (dybde / f)]."""
    u, v, d = cam.project(V)
    out = []
    for a, _b in obs:
        if axis == "col":
            m = np.abs(u - a) < 1.5
            k = np.argmax(np.where(m, v, -np.inf)) if m.any() else -1
        else:
            m = np.abs(v - a) < 1.5
            k = np.argmin(np.where(m, u, np.inf)) if m.any() else -1
        out.append((np.nan,) * 4 if k < 0 else (V[k, 0], V[k, 1], V[k, 2], d[k] / cam.f))
    return np.array(out)


def local_slope(x, y, half=4):
    s = np.full(len(x), np.nan)
    for i in range(len(x)):
        m = np.abs(x - x[i]) <= half
        if m.sum() >= 3:
            s[i] = np.polyfit(x[m], y[m], 1)[0]
    return s


if __name__ == "__main__":
    R = json.load(open(c.W + "/out/t9374_raw.json"))
    fr = np.asarray(R["front"], float)          # [v, u, red?]
    bo = np.asarray(R["bottom"], float)         # [u, v]
    bt = np.asarray(R["boottop"], float)
    VH, FH = U.hull_mesh(220, 60)
    VK, FK = G.keel_mesh()

    # ---- bunnen: kjolen
    cols = np.arange(150.0, 520.0, 1.0)
    _, hh = U.row_extents(CAM, VH, FH, cols, axis="col")
    _, hk = U.row_extents(CAM, VK, FK, cols, axis="col")
    keel_col = np.isfinite(hk) & (hk > hh - 3.0)
    u_keel = float(cols[keel_col].min())
    u_lim = u_keel - KEEL_MARGIN
    sling = (bo[:, 0] >= 396.0) & (bo[:, 0] <= 422.0)
    bo = bo[~sling & (bo[:, 0] <= u_lim)]
    bo = bo[robust_keep(bo[:, 0], bo[:, 1], 6, 2.5)]
    sl = local_slope(bo[:, 0], bo[:, 1])
    bottom = bo[np.abs(sl) < 1.0]

    # ---- forkanten: fra stevnens z = 300 ned, bare der kanten er bratt
    (xa, za), (xb, zb) = P.STEM_LINE
    x300 = xa + (300.0 - za) * (xb - xa) / (zb - za)
    v300 = float(CAM.project(np.array([[x300, 0.0, 300.0]]))[1][0])
    fr = fr[fr[:, 0] >= v300]
    fr = fr[robust_keep(fr[:, 0], fr[:, 1], 5, 2.0)]
    sl = local_slope(fr[:, 0], fr[:, 1])
    front = fr[np.abs(sl) < 1.0][:, :2]
    rows = np.arange(front[0, 0], front[-1, 0] + 1.0)
    lo_k, _ = U.row_extents(CAM, VK, FK, rows)        # jevnt rutenett (row_extents krever det)
    assert not np.any(np.isfinite(lo_k) & (lo_k < np.interp(rows, front[:, 0], front[:, 1]) + 5)), "kjolen naer stevnen?"

    # ---- stripen forut (x < 3 800), uten stroppen
    x38 = 3800.0
    u_bt = float(CAM.project(np.array([[x38, -G.side_y(x38, float(z_red(x38))), float(z_red(x38))]]))[0][0])
    r = bt[np.isfinite(bt[:, 4]) & (bt[:, 0] >= 160) & (bt[:, 0] <= u_bt)][:, [0, 4]]
    r = r[~((r[:, 0] >= 462) & (r[:, 0] <= 508))]
    r = r[robust_keep(r[:, 0], r[:, 1], 6, 1.5)]
    t = bt[np.isfinite(bt[:, 1]) & (bt[:, 0] >= 146) & (bt[:, 0] <= u_bt)][:, [0, 1]]
    t = t[~((t[:, 0] >= 462) & (t[:, 0] <= 508))]
    t = t[robust_keep(t[:, 0], t[:, 1], 6, 1.5)]

    xf = silhouette_pt(CAM, VH, FH, front, "row")
    xb_ = silhouette_pt(CAM, VH, FH, bottom, "col")
    out = dict(
        image="docs/foto/IMG_9374.jpg (= ~/Documents/Seilbaat/IMG_9374.jpeg), 761 x 472", W=761, H=472,
        camera="v10/verktoy/foto/out/cam9374.json, hovedkamera modes[main] = '%s' (geo9374.load_cam())" % CJ["main"],
        front=front,
        front_cols="[v, u]: per bilderad v, venstre kant av skroget (stevn/forfot) fra stevnens z = +300 "
                   "(rad %.1f) ned til kanten blir slakere enn 45 grader; over det roede er det skrog (hvitt/blaa "
                   "stripe) mot bakgrunn, i det roede venstre kant av bunnstoffet; subpiksel" % v300,
        front_x=xf[:, 0], front_xyz=xf[:, :3], front_mmpx=xf[:, 3],
        front_x_note="modellens silhuettpunkt i raden (dagens modell 13.11 kveld): x, (x, y, z) og mm per px "
                     "(dybde / f) - til regioner og omregning px -> mm",
        bottom=bottom,
        bottom_cols="[u, v]: per bildekolonne u, nederste kant av det roede (bunnens silhuett mot bryggeveggen, "
                    "vann og moerke ting bak), subpiksel; u %.0f-%.0f, bare der kanten er slakere enn 45 grader"
                    % (bottom[0, 0], bottom[-1, 0]),
        bottom_x=xb_[:, 0], bottom_xyz=xb_[:, :3], bottom_mmpx=xb_[:, 3],
        bottom_x_note="modellens silhuettpunkt i kolonnen (dagens modell): x, (x, y, z) og mm per px",
        bt_red=r,
        bt_red_cols="[u, v]: nedre kant av den lyse stripen (lys -> roedt) forut for x 3 800 (u <= %.0f), uten "
                    "stroppen (u 462-508); paa skroget ligger den i z_red(x) = 38 + %.1f + %.2f (x - 4000)/1000 "
                    "med dette kameraet (hoeyden er tilpasset aktenfor x 3 800, ikke her)" % (u_bt, DZR, KS),
        bt_top=t,
        bt_top_cols="[u, v]: blaa overkant forut; z_top(x) = bt_top_z(x) + %.1f + %.2f (x - 4000)/1000" % (DZT, KS),
        excluded=dict(sling_bottom_u=[396, 422], sling_stripe_u=[462, 508], keel_from_u=u_keel,
                      bottom_until_u=u_lim,
                      note="kolonner der modellens kjol (med hulkil) naar innen 3 px av skrogets silhuett "
                           "(u >= %.0f), minus %.0f px margin, er kuttet" % (u_keel, KEEL_MARGIN)),
        u_bt_max=u_bt, v_stem_z300=v300,
    )
    c.save_json(out, c.W + "/out/t9374_forkropp.json")
    print("front %d (rad %.1f-%.1f), bottom %d (u %.0f-%.0f), bt_red %d, bt_top %d; kjolen fra u %.0f, u_bt %.0f"
          % (len(front), front[0, 0], front[-1, 0], len(bottom), bottom[0, 0], bottom[-1, 0], len(r), len(t),
             u_keel, u_bt))
    print("x-omraade: front %.0f-%.0f, bunn %.0f-%.0f" % (np.nanmin(xf[:, 0]), np.nanmax(xf[:, 0]),
                                                        np.nanmin(xb_[:, 0]), np.nanmax(xb_[:, 0])))
