"""Forkroppen under vann i IMG_9387: sporing og utvalg -> ../out/t9387_forkropp.json.

Trenger ../out/t9387_cam.json (t9387.py) og ../out/cam9387.json (cam9387.py).

Omrisset av det roede (pluss stevnens kant gjennom stripen) fra stevnen ned
og akterover til like foran kjolen:
  front   per bilderad: venstre kant (stevn og forfot), rad 540-690
  bottom  per bildekolonne: nederste kant (bunnens silhuett), u 230 -> der
          kjolen (modellens kjol med kameraet) begynner aa danne omrisset
  bt_red  nedre kant av den lyse stripen (overgang til roedt) forut, u fra
          stevnen til x ~ 3 800
  bt_top  blaa overkant forut, samme utvalg (bare til orientering)
Luket bort: stativets kloss (u 735-815), roeret som krysser bunnen (u 812-862),
den roed-hvite stolpen bak (punkter langt under omrisset) og alt der kjolen
eller roret ville danne eller skjule omrisset.
Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python fk9387.py
"""
import json

import numpy as np

import common as c
import uwlib as U
import geo9387 as G
import t9387 as T

P, C = c.P, c.C
CJ = json.load(open(c.W + "/out/cam9387.json"))
CAM = U.Cam(CJ["p"], 2000, 1500)
DZT, DZR, KS = CJ["bt_dz_top"], CJ["bt_dz_red"], CJ["bt_slope_per_m"]


def z_red(x):
    return 38.0 + DZR + KS * (np.asarray(x, float) - 4000.0) / 1000.0


def z_top(x):
    return G.bt_top_z(np.asarray(x, float)) + DZT + KS * (np.asarray(x, float) - 4000.0) / 1000.0


def robust_keep(a, b, win=7, tol=3.5):
    """Behold punkter som ligger innen tol px fra glidende median."""
    keep = np.ones(len(a), bool)
    for i in range(len(a)):
        lo, hi = max(i - win, 0), min(i + win + 1, len(a))
        if abs(b[i] - np.median(b[lo:hi])) > tol:
            keep[i] = False
    return keep


def silhouette_x(cam, V, F, obs, axis):
    """Omtrentlig x paa modellens silhuettpunkt for hver observasjon (til
    regioner i summary): toppunktet som gir ytterpunktet i raden/kolonnen."""
    u, v, d = cam.project(V)
    xs = []
    for a, b in obs:
        if axis == "col":
            m = np.abs(u - a) < 2.0
            if not m.any():
                xs.append((np.nan, np.nan, np.nan, np.nan)); continue
            k = np.argmax(np.where(m, v, -np.inf))
        else:
            m = np.abs(v - a) < 2.0
            if not m.any():
                xs.append((np.nan, np.nan, np.nan, np.nan)); continue
            k = np.argmin(np.where(m, u, np.inf))
        xs.append((V[k, 0], V[k, 1], V[k, 2], d[k] / cam.f))
    return np.array(xs)


if __name__ == "__main__":
    tc = json.load(open(c.W + "/out/t9387_cam.json"))
    bt = np.asarray(tc["boottop"], float)
    stem_red, bot = T.trace_forebody(bt)
    bot_all = bot.copy()
    sf = T.trace_stem_front()
    kle, _, _ = T.trace_keel()

    # ---- front: stevnen gjennom stripen (sf) + roed kant (stem_red), per rad
    f1 = sf[(sf[:, 0] >= 540) & (sf[:, 0] <= 620)][:, :2]
    f2 = stem_red[(stem_red[:, 0] > 620) & (stem_red[:, 0] <= 690)]
    front = np.vstack([f1, f2])
    k = robust_keep(front[:, 0], front[:, 1], 5, 3.0)
    front = front[k]

    # ---- bottom: per kolonne
    bot = bot[(bot[:, 0] >= 230)]
    bad = ((bot[:, 0] >= 735) & (bot[:, 0] <= 815)) | ((bot[:, 0] >= 812) & (bot[:, 0] <= 862))
    bot = bot[~bad]
    k = robust_keep(bot[:, 0], bot[:, 1], 6, 3.5)
    bot = bot[k]

    # kjolen og roret: der deres nederste rad naar ned mot skrogets
    VH, FH = U.hull_mesh(220, 60)
    VK, FK = G.keel_mesh()
    VR, FR = G.rudder_mesh()
    cols = bot[:, 0]
    _, hh = U.row_extents(CAM, VH, FH, cols, axis="col")
    _, hk = U.row_extents(CAM, VK, FK, cols, axis="col")
    _, hr = U.row_extents(CAM, VR, FR, cols, axis="col")
    keel_col = np.isfinite(hk) & (hk > hh - 8.0)
    u_keel = float(cols[keel_col].min()) if keel_col.any() else 1e9
    # kjolens forkant i bildet (modellen): forste kolonne der kjolen synes under skroget
    allc = np.arange(600.0, 1300.0, 1.0)
    _, hh2 = U.row_extents(CAM, VH, FH, allc, axis="col")
    _, hk2 = U.row_extents(CAM, VK, FK, allc, axis="col")
    vis = np.isfinite(hk2) & (hk2 > hh2 + 1.0)
    u_keel_vis = float(allc[vis].min()) if vis.any() else 1e9
    u_lim = min(u_keel, u_keel_vis) - 25.0
    # i bildet: der det sporede omrisset boeyer ned i kjolens hulkil
    bot = bot[bot[:, 0] <= u_lim]
    print("kjolen danner omrisset fra u %.0f (modell), synlig under skroget fra u %.0f; bunnen brukt til u %.0f"
          % (u_keel, u_keel_vis, u_lim))
    lo_r, _ = U.row_extents(CAM, VK, FK, front[:, 0])
    assert not np.any(np.isfinite(lo_r) & (lo_r < front[:, 1] + 5)), "kjolen naer stevnen?"

    # ---- stripen forut
    u_bt = float(CAM.project(np.array([[3800.0, -G.side_y(3800.0, float(z_red(3800.0))), float(z_red(3800.0))]]))[0][0])
    r = bt[np.isfinite(bt[:, 4]) & (bt[:, 0] >= 165) & (bt[:, 0] <= u_bt)][:, [0, 4]]
    r = r[robust_keep(r[:, 0], r[:, 1], 6, 2.0)]
    t = bt[np.isfinite(bt[:, 1]) & (bt[:, 0] >= 85) & (bt[:, 0] <= u_bt)][:, [0, 1]]
    t = t[robust_keep(t[:, 0], t[:, 1], 6, 2.0)]

    # kjolroten (bare til vurdering, ikke i resid): omrisset fra bunnen ned i
    # kjolens forkant, per rad 800-860 og per kolonne fra bunnens siste punkt
    root_rows = kle[(kle[:, 0] >= 800) & (kle[:, 0] <= 860)]
    root_cols = bot_all[(bot_all[:, 0] > u_lim) & (bot_all[:, 0] <= 960)]
    root_cols = root_cols[robust_keep(root_cols[:, 0], root_cols[:, 1], 4, 3.5)]

    xf = silhouette_x(CAM, VH, FH, front, "row")
    xb = silhouette_x(CAM, VH, FH, bot, "col")
    out = dict(
        image="docs/foto/IMG_9387.jpg", W=2000, H=1500, camera="v10/verktoy/foto/out/cam9387.json (p)",
        front=front, front_cols="[v, u]: per bilderad v (rad 540-690), venstre kant av skroget (stevn/forfot); "
                                "rad 540-620 fargekant i stripen (blaa/lys/moerk roed mot hvitt skrog bak), "
                                "rad 621-690 venstre kant av det roede",
        front_x=xf[:, 0], front_xyz=xf[:, :3], front_mmpx=xf[:, 3],
        front_x_note="modellens silhuettpunkt i raden (dagens modell, 13.11 kveld): x, (x,y,z) og mm per px "
                     "(dybde/f) - til regioner og omregning px -> mm",
        bottom=bot, bottom_cols="[u, v]: per bildekolonne u, nederste kant av det roede (bunnens silhuett mot "
                                "blaa baat / asfalt), subpiksel; u %.0f-%.0f uten stativ og roer" % (bot[0, 0], bot[-1, 0]),
        bottom_x=xb[:, 0], bottom_xyz=xb[:, :3], bottom_mmpx=xb[:, 3],
        bottom_x_note="modellens silhuettpunkt i kolonnen (dagens modell): x, (x,y,z) og mm per px",
        bt_red=r, bt_red_cols="[u, v]: nedre kant av den lyse stripen (lys -> roedt), forut for x 3 800 "
                              "(u <= %.0f); paa skroget ligger den i z_red(x) = 38 + %.1f + %.2f (x-4000)/1000 "
                              "med dette kameraet" % (u_bt, DZR, KS),
        bt_top=t, bt_top_cols="[u, v]: blaa overkant forut; z_top(x) = bt_top_z(x) + %.1f + %.2f (x-4000)/1000" % (DZT, KS),
        root_rows=root_rows, root_rows_cols="[v, u]: kjolroten, venstre kant av det roede per rad 800-860 "
                                             "(hulkil/forkant; modellen her = skrog + kjol)",
        root_cols=root_cols, root_cols_cols="[u, v]: kjolroten, nederste roede rad per kolonne fra bunnens siste "
                                            "brukte kolonne til u 960",
        stem_above=np.asarray(tc["stem_top"], float)[:, :2],
        stem_above_cols="[v, u]: stevnens kant over stripen (rad 476-534), brukt i kameraet (z > 260)",
        excluded=dict(stand_block_u=[735, 815], pipe_u=[812, 862], keel_from_u=u_lim,
                      note="kolonner der modellens kjol (med hulkil) naar innen 8 px av skrogets silhuett, "
                           "minus 25 px margin, er kuttet"),
        u_bt_max=u_bt, keel_u_model=u_keel, keel_u_visible=u_keel_vis,
    )
    c.save_json(out, c.W + "/out/t9387_forkropp.json")
    print("front", len(front), "bottom", len(bot), "bt_red", len(r), "bt_top", len(t), "u_bt %.0f" % u_bt)
