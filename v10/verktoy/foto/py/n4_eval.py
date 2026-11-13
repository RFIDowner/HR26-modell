"""Svar paa spoersmaalene 1-5 fra «nye (4).jpeg» med kameraene i
../out/n4_cam.json (dagens modell = arbeidstreet). Fortegn som e9374.py:
+ = modellen ligger UTENFOR bildets omriss (dypere bunn, lenger forut forfot,
dypere kjol/ror).

  1 bunn     skrogets nedre silhuett per kolonne (u 170-546 utenom stoetter),
             modell_v - foto_v, i px og mm (loddrett), samlet per 0,25 m i x
  2 forfot   forkant per rad (rad 514-566): foto_u - modell_u (mm langs x ved
             fast z) og normalt paa profilen; pluss bunnen x 0,9-1,5 m
  3 kjol     bunn per kolonne (mm loddrett), forkant og bakkant per rad (mm i x),
             og avstanden listens underkant -> kjolens bunn ved x 4 600
  4 ror      bunn per kolonne (z), forkant/bakkant per rad (x), korden nederst
  5 vindu    endenes x i bildet mot P.WIN_X0/WIN_X1 (ramme-endene som i
             geo9374.window_ends); stripen: z for blaa overkant, blaa underkant
             og roedt start paa skrogsiden, og avstanden fra listens underkant

Lagrer ../out/n4_eval.json og skriver en tabell per kameravariant.

  python ../../../../tools/memcap.py --gb 3 --lock -- python n4_eval.py
"""
import json

import numpy as np

import common as c
import uwlib as U
import geo9374 as G
import n4_cam as K

P, C = c.P, c.C
T = K.T
VH, FH = K.VH, K.FH
_Vf = VH[FH]
F_BOT = FH[(_Vf[:, :, 0].max(1) < 3500.0) & (_Vf[:, :, 2].max(1) < 700.0)]
F_FRONT = FH[(_Vf[:, :, 0].max(1) < 2600.0) & (_Vf[:, :, 2].max(1) < 500.0)]
VK, FK = K.VK, K.FK
VR, FR = G.rudder_mesh()

BOT = np.asarray(T["bottom"], float)
BOT = np.r_[BOT[BOT[:, 0] < 560], np.asarray(T["bottom_dark"], float)]
BOT = BOT[np.argsort(BOT[:, 0])]
# over rad 514 er det ytre roede omrisset den andre baatens forfot (bak vaar stevn), ikke vaar
BOT = BOT[BOT[:, 1] >= 514.0]
FRONT = np.asarray(T["front"], float)[:, :2]
SWL = np.asarray(T["stem_wl"], float)
KLE = np.asarray(T["keel_le"], float)
KTE = np.asarray(T["keel_te"], float)
KBO = np.asarray(T["keel_bot"], float)
RU = np.asarray(T["rudder"], float)
RB = np.asarray(T["rudder_bot"], float)
BTT = np.asarray(T["boottop"], float)
WIN = T["window"]
STRK = np.asarray(T["strake"], float)

XP = np.linspace(400.0, 3600.0, 801)
PROF = np.c_[XP, np.zeros_like(XP), [C.bottom_z(x) for x in XP]]     # kjollinja (kanobunnen) i senterplanet


def mm_per_px(cam, X, d):
    """mm per px langs retningen d (3-vektor, mm) i punktet X."""
    X = np.atleast_2d(X)
    u0, v0, _ = cam.project(X)
    u1, v1, _ = cam.project(X + 10.0 * np.asarray(d, float))
    return 10.0 / np.hypot(u1 - u0, v1 - v0)


def prof_x_of_u(cam):
    u, v, _ = cam.project(PROF)
    o = np.argsort(u)
    return lambda uu: np.interp(uu, u[o], XP[o], left=np.nan, right=np.nan)


def prof_x_of_v(cam, x0=500.0, x1=1700.0):
    m = (XP >= x0) & (XP <= x1)
    u, v, _ = cam.project(PROF[m])
    o = np.argsort(v)
    return lambda vv: np.interp(vv, v[o], XP[m][o], left=np.nan, right=np.nan)


def bins(x, r, edges):
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = np.isfinite(x) & (x >= a) & (x < b) & np.isfinite(r)
        out.append(dict(x0=a, x1=b, n=int(m.sum()), mean=float(np.median(r[m])) if m.any() else None,
                        sd=float(1.4826 * np.median(np.abs(r[m] - np.median(r[m])))) if m.sum() > 2 else None))
    return out


def q1_bottom(cam):
    lo, hi = U.row_extents(cam, VH, F_BOT, BOT[:, 0], axis="col")
    r = np.where(np.isfinite(hi), hi - BOT[:, 1], np.nan)
    xu = prof_x_of_u(cam)(BOT[:, 0])
    s = np.array([mm_per_px(cam, [x, 0.0, C.bottom_z(x)], [0, 0, 1])[0] if np.isfinite(x) else np.nan for x in xu])
    mm = r * s
    edges = [900, 1200, 1500, 1750, 2000, 2250, 2500, 2750, 3000]
    return dict(u=BOT[:, 0], x=xu, px=r, mm=mm, bins=bins(xu, mm, edges), bins_px=bins(xu, r, edges))


def q2_front(cam):
    lo, hi = U.row_extents(cam, VH, F_FRONT, FRONT[:, 0])
    r = np.where(np.isfinite(lo), FRONT[:, 1] - lo, np.nan)            # + = modellen lenger forut
    xv = prof_x_of_v(cam)(FRONT[:, 0])
    z = np.array([C.bottom_z(x) if np.isfinite(x) else np.nan for x in xv])
    s = np.array([mm_per_px(cam, [x, 0.0, zz], [1, 0, 0])[0] if np.isfinite(x) else np.nan for x, zz in zip(xv, z)])
    mm = r * s
    # profilens helning -> normalavstand n = dx * sin(theta)
    dz = np.gradient([C.bottom_z(x) for x in XP], XP)
    th = np.arctan(np.abs(np.interp(xv, XP, dz)))
    nmm = mm * np.sin(th)
    # stevnen ved stripen (kontroll, z ~ +100..+250 paa land)
    lo2, _ = U.row_extents(cam, VH, FH[(_Vf[:, :, 0].max(1) < 1600.0)], SWL[:, 0])
    rw = SWL[:, 1] - lo2
    return dict(v=FRONT[:, 0], x=xv, z=z, px=r, mm_x=mm, mm_n=nmm,
                bins=bins(xv, mm, [700, 900, 1100, 1300, 1500, 1700]),
                bins_n=bins(xv, nmm, [700, 900, 1100, 1300, 1500, 1700]),
                stem_wl_px=rw)


def q3_keel(cam):
    out = {}
    _, hi = U.row_extents(cam, VK, FK, KBO[:, 0], axis="col")
    r = hi - KBO[:, 1]                                                   # + = modellens kjol dypere
    # x langs bunnen: kjolens bunnlinje (x, -120, -1400)
    xb = np.linspace(4000.0, 5800.0, 200)
    u, v, _ = cam.project(np.c_[xb, np.full(200, -120.0), np.full(200, -1400.0)])
    xk = np.interp(KBO[:, 0], u, xb)
    s = mm_per_px(cam, np.c_[xk, np.full(len(xk), -120.0), np.full(len(xk), -1400.0)], [0, 0, 1])
    out["bot"] = dict(u=KBO[:, 0], x=xk, px=r, mm=r * s)
    lo, _ = U.row_extents(cam, VK, FK, KLE[:, 0])
    rl = KLE[:, 1] - lo                                                  # + = modellens forkant lenger forut
    _, hi = U.row_extents(cam, VK, FK, KTE[:, 0])
    rt = hi - KTE[:, 1]                                                  # + = modellens bakkant lenger akter
    sx = mm_per_px(cam, [4800.0, 0.0, -1000.0], [1, 0, 0])[0]
    # z per rad (senterplanet ved x ~ forkant/bakkant)
    zz = np.linspace(-1400.0, -300.0, 300)
    _, vle, _ = cam.project(np.c_[np.full(300, 3900.0), np.zeros(300), zz])
    _, vte, _ = cam.project(np.c_[np.full(300, 5700.0), np.zeros(300), zz])
    rl = np.where(np.isfinite(rl), rl, np.nan)
    rt = np.where(np.isfinite(rt), rt, np.nan)
    out["le"] = dict(v=KLE[:, 0], z=np.interp(KLE[:, 0], vle[::-1], zz[::-1]), px=rl, mm=rl * sx)
    out["te"] = dict(v=KTE[:, 0], z=np.interp(KTE[:, 0], vte[::-1], zz[::-1]), px=rt, mm=rt * sx)
    m = (xk > 4300) & (xk < 5000)
    dmm = float(np.mean(out["bot"]["mm"][m])) if m.any() else float(np.mean(out["bot"]["mm"]))
    under = C.strake_z(4600.0) - 0.5 * P.STRAKE_H
    out["depth"] = dict(model=float(under + 1400.0), photo=float(under + 1400.0 - dmm), dmm=dmm,
                        dmm_all=float(np.mean(out["bot"]["mm"])))
    return out


def q4_rudder(cam):
    out = {}
    _, hi = U.row_extents(cam, VR, FR, RB[:, 0], axis="col")
    r = hi - RB[:, 1]
    s = mm_per_px(cam, [8000.0, 0.0, P.RUDDER_BOT_Z], [0, 0, 1])[0]
    m = np.isfinite(r)
    # bare den flate delen av bunnen (ikke det runde hjoernet ved forkanten)
    mm = r * s
    # mm > 0: modellens bunn lavere i bildet = dypere enn rorets bunn i bildet
    out["bot"] = dict(u=RB[:, 0], px=r, mm=mm, z_photo=float(P.RUDDER_BOT_Z + np.nanmedian(mm[m])))
    lo, hi = U.row_extents(cam, VR, FR, RU[:, 0])
    sx = mm_per_px(cam, [7900.0, 0.0, -600.0], [1, 0, 0])[0]
    lo = np.where(np.isfinite(lo), lo, np.nan)
    hi = np.where(np.isfinite(hi), hi, np.nan)
    rl = RU[:, 1] - lo                     # + = modellens forkant lenger forut (korden lengre forover)
    rt = hi - RU[:, 2]                     # + = modellens bakkant lenger akter
    zz = np.linspace(P.RUDDER_BOT_Z - 50.0, 0.0, 200)
    _, vv, _ = cam.project(np.c_[np.full(200, 7900.0), np.zeros(200), zz])
    z = np.interp(RU[:, 0], vv[::-1], zz[::-1])
    out["le"] = dict(v=RU[:, 0], z=z, px=rl, mm=rl * sx)
    out["te"] = dict(v=RU[:, 0], z=z, px=rt, mm=rt * sx)
    # korden i bildet og i modellen i samme rad (rader over det runde hjoernet)
    ch_ph = (RU[:, 2] - RU[:, 1]) * sx
    ch_mod = (hi - lo) * sx
    out["chord"] = dict(z=z, photo=ch_ph, model=ch_mod)
    return out


def window_x(cam, obs_u, z_of_x, x0, x1):
    xs = np.linspace(x0, x1, 400)
    pts = np.array([[x, -G.side_y(x, z_of_x(x)), z_of_x(x)] for x in xs])
    u, v, _ = cam.project(pts)
    return float(np.interp(obs_u, u, xs))


def q5_window(cam):
    W3 = G.window_ends()
    u, v, _ = cam.project(W3)
    rf, ra = P.WIN_RAKE
    zf = lambda x: 0.5 * (C.strake_z(x) + P.WIN_ABOVE_STRAKE + C.sheer_z(x) - P.WIN_BELOW_DECK)
    za = lambda x: C.strake_z(x) + P.WIN_ABOVE_STRAKE + 25.0
    xf = window_x(cam, WIN["fwd_end"][0], zf, 2500.0, 5000.0)
    xa = window_x(cam, WIN["aft_end"][0], za, 4300.0, 6800.0)
    return dict(model_x=[float(W3[0, 0]), float(W3[1, 0])], photo_x=[xf, xa], dx=[xf - W3[0, 0], xa - W3[1, 0]],
                px_u=[float(WIN["fwd_end"][0] - u[0]), float(WIN["aft_end"][0] - u[1])],
                px_v=[float(WIN["fwd_end"][1] - v[0]), float(WIN["aft_end"][1] - v[1])],
                win_x0_photo=xf - 0.5 * rf * 0.6, win_x1_photo=xa + 15.0)


def q5_stripe(cam, xs_eval=(2500.0, 3500.0, 4600.0, 5500.0, 6500.0)):
    zs = np.arange(-150.0, 501.0, 25.0)
    lines = []
    for z in zs:
        L = G.zline3(lambda x, z=z: z, 1500.0, 7700.0, 160)
        u, v, _ = cam.project(L)
        o = np.argsort(u)
        lines.append((u[o], v[o], L[o, 0]))
    res = {}
    for j, name in ((1, "blue_top"), (2, "blue_bot"), (3, "red_top")):
        ok = np.isfinite(BTT[:, j])
        uu, vv = BTT[ok, 0], BTT[ok, j]
        zmat = np.array([np.interp(uu, a, b, left=np.nan, right=np.nan) for a, b, _ in lines])   # v(z) per kolonne
        xmat = np.array([np.interp(uu, a, xx, left=np.nan, right=np.nan) for a, _, xx in lines])
        zp, xp = [], []
        for k in range(len(uu)):
            col = zmat[:, k]
            if not np.isfinite(col).all():
                zp.append(np.nan); xp.append(np.nan); continue
            o = np.argsort(col)
            z = float(np.interp(vv[k], col[o], zs[o]))
            zp.append(z)
            xp.append(float(np.interp(z, zs, xmat[:, k])))
        zp, xp = np.array(zp), np.array(xp)
        under = np.array([C.strake_z(x) - 0.5 * P.STRAKE_H if np.isfinite(x) else np.nan for x in xp])
        dist = under - zp
        at = {}
        for xe in xs_eval:
            m = np.abs(xp - xe) < 250
            at[str(int(xe))] = dict(z=float(np.nanmean(zp[m])) if m.any() else None,
                                    under_strake=float(np.nanmean(dist[m])) if m.any() else None)
        res[name] = dict(u=uu, x=xp, z=zp, dist=dist, at=at)
    return res


def evaluate(cam):
    return dict(q1=q1_bottom(cam), q2=q2_front(cam), q3=q3_keel(cam), q4=q4_rudder(cam), q5w=q5_window(cam),
                q5s=q5_stripe(cam))


def fmt_bins(b, key="mean"):
    return " ".join("%s" % ("   -  " if d[key] is None else "%+5.0f" % d[key]) for d in b)


if __name__ == "__main__":
    J = json.load(open(c.W + "/out/n4_cam.json"))
    allres = {}
    for tag, d in J["modes"].items():
        cam = K.make_cam(np.asarray(d["q"], float), d["cmode"])
        e = evaluate(cam)
        allres[tag] = e
        q = d["q"]
        print("=== %s  C=(%.0f, %.0f, %.0f) f %.0f  %s  rms %s" % (
            tag, q[0], q[1], q[2], q[6], {k: round(float(v), 3) for k, v in d["extra"].items()},
            {k: round(v, 1) for k, v in d["rms"].items()}))
        print("  1 bunn mm (x 0.9|1.2|1.5|1.75|2.0|2.25|2.5|2.75-3.0):", fmt_bins(e["q1"]["bins"]),
              "  n", [b["n"] for b in e["q1"]["bins"]])
        print("  2 forfot mm langs x (x .7|.9|1.1|1.3|1.5-1.7):", fmt_bins(e["q2"]["bins"]), " normalt:",
              fmt_bins(e["q2"]["bins_n"]), " stevn ved stripen px %+.1f" % np.nanmean(e["q2"]["stem_wl_px"]))
        k3 = e["q3"]
        print("  3 kjol: bunn %+.0f mm (x 4.3-5.0; alle %+.0f), forkant %+.0f mm, bakkant %+.0f mm (median); "
              "liste-underkant -> kjolbunn: modell %.0f, foto %.0f"
              % (k3["depth"]["dmm"], k3["depth"]["dmm_all"], np.nanmedian(k3["le"]["mm"]), np.nanmedian(k3["te"]["mm"]),
                 k3["depth"]["model"], k3["depth"]["photo"]))
        r4 = e["q4"]
        m = r4["chord"]["z"] < -700
        print("  4 ror: bunn z foto %.0f (modell %.0f); forkant %+.0f mm, bakkant %+.0f mm; korde z<-700 foto %.0f "
              "modell %.0f" % (r4["bot"]["z_photo"], P.RUDDER_BOT_Z, np.nanmean(r4["le"]["mm"]),
                               np.nanmean(r4["te"]["mm"]), np.nanmean(r4["chord"]["photo"][m]),
                               np.nanmean(r4["chord"]["model"][m])))
        w = e["q5w"]
        print("  5 vindu: forende x foto %.0f (modell %.0f, %+.0f), akterende foto %.0f (modell %.0f, %+.0f); "
              "v-rest %+.1f/%+.1f px" % (w["photo_x"][0], w["model_x"][0], w["dx"][0], w["photo_x"][1],
                                          w["model_x"][1], w["dx"][1], w["px_v"][0], w["px_v"][1]))
        s = e["q5s"]
        print("  5 stripe x 4600: blaa overkant z %.0f (%.0f under listens underkant), blaa underkant z %.0f (%.0f), "
              "roedt z %.0f (%.0f)" % tuple(v for n in ("blue_top", "blue_bot", "red_top")
                                            for v in (s[n]["at"]["4600"]["z"], s[n]["at"]["4600"]["under_strake"])))
    c.save_json(dict(modes=allres, main=J["main"]), c.W + "/out/n4_eval.json")
