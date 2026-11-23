"""Maalinger i «nye (6).jpeg» mot modellen (arbeidstreet), for hver
kameravariant i ../out/n6_cam.json. Lager ../out/n6_meas.json.

  1 ror        sporet omriss tilbakeprojisert til rorets plan (y = +25):
               bunnens z, bakkant og forkant x(z), trinnet under skroget
  2 akter      skrogets nedre omriss mellom roret og kjolen, tilbakeprojisert
               til senterplanet, mot modellens senterprofil (curves.bottom_z)
               og mot modellens eget omriss (nettets silhuett) per 0,25 m
  3 kjol       kjolens bunn og bakkant mot modellens silhuett (px -> mm med
               lokal skala), og listen over kjolen; dybden fra listens
               underkant til kjolbunnen = 2 203 + e_liste - e_kjol
  4 vindu      vindusendene tilbakeprojisert til skrogsiden (x)
    akterspeil hjoernet (sporet) mot modellen; listens gummiende paa akterspeilet

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 --lock -- python n6_meas.py
"""
import json
import sys

import numpy as np

import common as c
import uwlib as U
import n6_geo as N
import n6_cam as K
import geo9374 as G

P, C = N.P, N.C
T = K.T
VH, FH = N.hull_mesh(220, 60)
VK, FK = K.VK, K.FK


def arr(k):
    return np.asarray(T[k], float)


def ray_plane_y(cam, uv, y0):
    d = cam.ray(uv[:, 0], uv[:, 1])
    t = (y0 - cam.C[1]) / d[:, 1]
    return cam.C[None, :] + t[:, None] * d


def ray_surface(cam, uv, fsurf, t0=500.0, t1=20000.0, n=400):
    """Foerste skjaering langs strålen med flaten fsurf(P) = 0 (fortegnsskifte)."""
    d = cam.ray(uv[:, 0], uv[:, 1])
    out = []
    ts = np.linspace(t0, t1, n)
    for di in d:
        Ps = cam.C[None, :] + ts[:, None] * di[None, :]
        fv = np.array([fsurf(p) for p in Ps])
        ok = np.isfinite(fv)
        hit = None
        for i in range(len(ts) - 1):
            if ok[i] and ok[i + 1] and fv[i] * fv[i + 1] <= 0:
                a, b = ts[i], ts[i + 1]
                fa = fv[i]
                for _ in range(40):
                    m = 0.5 * (a + b)
                    fm = fsurf(cam.C + m * di)
                    if not np.isfinite(fm):
                        break
                    if fa * fm <= 0:
                        b = m
                    else:
                        a, fa = m, fm
                hit = cam.C + 0.5 * (a + b) * di
                break
        out.append(hit if hit is not None else np.full(3, np.nan))
    return np.array(out)


def side_surf(p):
    y = G.side_y(p[0], p[2])
    return p[1] - y


def transom_surf(p):
    return p[0] - C.transom_x(p[2], p[1])


def vscale(cam, X, dz=100.0):
    """px per mm nedover (v) for en hoeydeendring ved punktet X."""
    a = cam.project(np.array([X, X + [0.0, 0.0, dz]], float))
    return (a[1][0] - a[1][1]) / dz


def uscale_x(cam, X, dx=100.0):
    a = cam.project(np.array([X, X + [dx, 0.0, 0.0]], float))
    return (a[0][1] - a[0][0]) / dx


def measure(q, cfg):
    G._SEC_CACHE.clear()          # side_y-hurtigbufferen vokser med hver straale (minnetaket)
    cam = K.make_cam(np.asarray(q, float), cfg["mode"])
    out = {}

    # ---------------------------------------------------------------- 1 roret
    yr = 25.0
    bot = ray_plane_y(cam, arr("rud_bot"), yr)
    te = ray_plane_y(cam, arr("rud_te")[:, ::-1], yr)
    le = ray_plane_y(cam, arr("rud_le")[:, ::-1], yr)
    st = arr("rud_step"); st = st[st[:, 0] <= 312]
    stp = ray_plane_y(cam, st, yr)
    gap = arr("rud_gap"); gap = gap[gap[:, 2] > 8.0][:, :2]
    gp = ray_plane_y(cam, gap[:, ::-1], 0.0)
    # bunnen: flat del (u 120-215), og laveste punkt
    bm = (arr("rud_bot")[:, 0] >= 120) & (arr("rud_bot")[:, 0] <= 215)

    def fit_x(Pz, z):
        k = np.polyfit(Pz[:, 2], Pz[:, 0], 1)
        return float(np.polyval(k, z)), float(k[0])
    out["rudder"] = dict(
        bot_z_mean=float(np.mean(bot[bm, 2])), bot_z_min=float(bot[:, 2].min()),
        bot_x_range=[float(bot[:, 0].min()), float(bot[:, 0].max())],
        te_x_at=dict((str(z), fit_x(te, z)[0]) for z in (-200.0, -600.0, -1000.0)),
        te_dxdz=fit_x(te, -600.0)[1],
        le_low_x_at=dict((str(z), fit_x(le, z)[0]) for z in (-700.0, -900.0)),
        le_low_dxdz=fit_x(le, -800.0)[1],
        le_low_top=[float(le[0, 0]), float(le[0, 2])],
        step_z_mean=float(np.mean(stp[:, 2])), step_x_range=[float(stp[:, 0].min()), float(stp[:, 0].max())],
        gap_x_at=dict((str(z), fit_x(gp, z)[0]) for z in (-100.0, -300.0)) if len(gp) > 5 else None,
        te_pts=te[::20], le_pts=le[::20], bot_pts=bot[::15], step_pts=stp[::10],
        model=dict(bot_z=P.RUDDER_BOT_Z, te_x=P.RUDDER_TE_X, le_top_x=P.RUDDER_X, le_bot_x=P.RUDDER_X + P.RUDDER_RAKE,
                   top_z=P.RUDDER_TOP_Z))

    # ---------------------------------------------------------------- 2 akter for kjolen
    ab = arr("aft_bot")
    ab = ab[(ab[:, 0] >= 338) & (ab[:, 0] <= 606)]
    Pp = ray_plane_y(cam, ab, 0.0)
    cols = np.arange(252.0, 640.0, 1.0)
    lo, hi = U.row_extents(cam, VH, FH, cols, axis="col")
    okm = np.isfinite(hi)
    Pm = ray_plane_y(cam, np.c_[cols[okm], hi[okm]], 0.0)
    zc_p = np.array([C.bottom_z(float(x)) for x in Pp[:, 0]])
    bins = []
    for x0 in np.arange(5500.0, 8000.0, 250.0):
        m = (Pp[:, 0] >= x0) & (Pp[:, 0] < x0 + 250.0)
        mm = (Pm[:, 0] >= x0) & (Pm[:, 0] < x0 + 250.0)
        if m.sum() < 3:
            continue
        zp = float(np.median(Pp[m, 2]))
        zcl = float(np.median(zc_p[m]))
        zsil = float(np.median(Pm[mm, 2])) if mm.sum() >= 3 else float("nan")
        # i piksler: sporet mot modellens silhuett i samme kolonner
        uu = ab[m, 0]
        hv = np.interp(uu, cols[okm], hi[okm])
        dv = float(np.median(ab[m, 1] - hv))
        Xm = np.array([np.median(Pp[m, 0]), 0.0, zcl])
        s = vscale(cam, Xm)
        bins.append(dict(x0=x0, x1=x0 + 250.0, n=int(m.sum()), z_photo=zp, z_model_cl=zcl, z_model_sil=zsil,
                         d_cl=zp - zcl, d_sil=(zp - zsil) if np.isfinite(zsil) else None, dv_px=dv,
                         d_px_mm=-dv / s, px_per_mm=s))
    out["aft"] = bins

    # ---------------------------------------------------------------- 3 kjolen
    kb = arr("keel_bot")
    kb = kb[(kb[:, 0] >= 630) & (kb[:, 0] <= 780)]
    lo, hi = U.row_extents(cam, VK, FK, kb[:, 0], axis="col")
    ok = np.isfinite(hi)
    Pk = ray_plane_y(cam, kb[ok], 75.0)
    dvk = kb[ok, 1] - hi[ok]
    sk = np.array([vscale(cam, np.array([x, 75.0, -1400.0])) for x in Pk[:, 0]])
    ek = -dvk / sk                       # z_foto - z_modell, kjolbunnen
    kt = arr("keel_te")
    kt = kt[(kt[:, 0] >= 1150) & (kt[:, 0] <= 1268)]
    lo, hi = U.row_extents(cam, VK, FK, kt[:, 0])
    ok2 = np.isfinite(lo)
    du = kt[ok2, 1] - lo[ok2]
    ux = np.array([uscale_x(cam, np.array([5700.0, 100.0, float(z)])) for z in
                   ray_plane_y(cam, kt[ok2][:, ::-1], 100.0)[:, 2]])
    ex_te = du / ux                      # x_foto - x_modell, bakkanten
    Pte = ray_plane_y(cam, kt[ok2][:, ::-1], 100.0)
    kl = arr("keel_le")
    kl = kl[(kl[:, 0] >= 1110) & (kl[:, 0] <= 1235)]
    lo, hi = U.row_extents(cam, VK, FK, kl[:, 0])
    ok3 = np.isfinite(hi)
    ex_le = (kl[ok3, 1] - hi[ok3]) / np.array([uscale_x(cam, np.array([4000.0, 100.0, -1000.0]))] * ok3.sum())
    # listen over kjolen: residual i v -> mm
    so = K.OBS["strake"]
    rs = K.curve_resid(cam, K.NEAR3, so)            # pred - obs (px)
    u46, v46, _ = cam.project(np.array([[4600.0, 1340.0, C.strake_z(4600.0)], [5200.0, 1340.0, C.strake_z(5200.0)]]))
    sel = (so[:, 0] >= min(u46) - 15) & (so[:, 0] <= max(u46) + 15)
    s_s = vscale(cam, np.array([4900.0, 1330.0, 830.0]))
    es = float(np.median(rs[sel])) / s_s if sel.sum() else float("nan")   # z_foto - z_modell for listen
    depth_model = (C.strake_z(4600.0) - 0.5 * P.STRAKE_H) - P.KEEL_TIP_Z
    out["keel"] = dict(e_bot_mm=float(np.median(ek)), e_bot_spread=[float(np.percentile(ek, 10)),
                                                                       float(np.percentile(ek, 90))],
                       bot_x_range_photo=[float(Pk[:, 0].min()), float(Pk[:, 0].max())],
                       e_bot_vs_x=np.c_[Pk[::10, 0], ek[::10]],
                       e_strake_mm=es, n_strake=int(sel.sum()),
                       depth_model=float(depth_model), depth_photo=float(depth_model + es - np.median(ek)),
                       e_te_mm=float(np.median(ex_te)), e_te_low_mm=float(np.median(ex_te[-30:])),
                       te_pts=Pte[::15], e_le_mm=float(np.median(ex_le)) if ok3.sum() else None)

    # ---------------------------------------------------------------- 4 vinduet og akterspeilet
    w = T["window"]
    pts = np.array([w["aft_end"], w["aft_top"], w["aft_bot"], w["fwd_top"], w["fwd_end"]], float)
    Pw = ray_surface(cam, pts, side_surf)
    out["window"] = dict(names=["aft_end", "aft_top", "aft_bot", "fwd_top", "fwd_end"], pts=Pw,
                         model=dict(x0_bot=P.WIN_X0, x0_top=P.WIN_X0 + P.WIN_RAKE[0], x1_bot=P.WIN_X1,
                                    x1_top=P.WIN_X1 - P.WIN_RAKE[1]))
    tc = K.OBS["corner"]
    dc = K.poly_dist(cam, K.CORNER3, tc)
    out["corner"] = dict(upper_px=float(np.median(dc[tc[:, 1] < 830])), lower_px=float(np.median(dc[tc[:, 1] > 830])),
                         by_v=np.c_[tc[::6, 1], dc[::6]])
    rub = ray_surface(cam, np.array([T["corner"]["near_rubber_end"], T["corner"]["far_end"]], float), transom_surf)
    out["strake_end"] = dict(near_rubber_end=rub[0], far_end=rub[1])
    # vinduet i piksler: modellens ender projisert mot de haandleste
    wm = np.array([[P.WIN_X1, 0.0, C.strake_z(P.WIN_X1) + P.WIN_ABOVE_STRAKE],
                   [P.WIN_X1 - P.WIN_RAKE[1], 0.0, C.sheer_z(P.WIN_X1) - P.WIN_BELOW_DECK],
                   [P.WIN_X0, 0.0, C.strake_z(P.WIN_X0) + P.WIN_ABOVE_STRAKE],
                   [P.WIN_X0 + P.WIN_RAKE[0], 0.0, C.sheer_z(P.WIN_X0) - P.WIN_BELOW_DECK]])
    wm[:, 1] = [G.side_y(x, z) for x, z in wm[:, [0, 2]]]
    uw, vw, _ = cam.project(wm)
    obs_w = np.array([w["aft_bot"], w["aft_top"], w["fwd_end"], w["fwd_top"]], float)
    out["window"]["px_model_minus_photo"] = np.c_[uw - obs_w[:, 0], vw - obs_w[:, 1]]
    out["window"]["mm_per_px_x"] = [1.0 / abs(uscale_x(cam, wm[i])) for i in range(4)]
    # vannlinjestripens overkant: hoeyden i modellens ramme (tilbakeprojisert)
    btp = np.asarray(T["boottop"], float)
    s1 = btp[np.isfinite(btp[:, 1]) & (btp[:, 0] >= 500) & (btp[:, 0] <= 860)][::10]
    Ps = ray_surface(cam, s1[:, :2], side_surf, 2000.0, 15000.0, 200)
    s2 = btp[np.isfinite(btp[:, 1]) & (btp[:, 0] >= 130) & (btp[:, 0] <= 235)][::5]
    Pr = ray_plane_y(cam, s2[:, :2], 0.0)
    out["boottop"] = dict(side_z=float(np.nanmedian(Ps[:, 2])), side_x=[float(np.nanmin(Ps[:, 0])), float(np.nanmax(Ps[:, 0]))],
                          rudder_z=float(np.median(Pr[:, 2])),
                          afloat_ref="IMG_9370: blaa overkant 146 (x 1000) -> 125 (x 5500 og akterover)")
    # akterspeilets hjoerne tilbakeprojisert til akterspeilsflaten: (y, z)
    Pc = ray_surface(cam, tc, transom_surf, 1000.0, 15000.0, 300)
    out["corner"]["photo_yz"] = Pc[::4, 1:]
    out["corner"]["model_y_at_photo_z"] = np.array([np.interp(z, K.CORNER3[:, 2], K.CORNER3[:, 1])
                                                    for z in Pc[::4, 2]])
    g = K.residuals(np.asarray(q, float), cfg, True)
    out["rms"] = {k: float(np.sqrt(np.mean(np.square(v)))) for k, v in g.items()}
    return out


if __name__ == "__main__":
    J = json.load(open(c.W + "/out/n6_cam.json"))["modes"]
    names = sys.argv[1:] or list(J)
    res = {}
    for nm in names:
        d = J[nm]
        r = measure(d["q"], d["cfg"])
        res[nm] = r
        G._SEC_CACHE.clear()
        try:
            old = json.load(open(c.W + "/out/n6_meas.json"))
        except OSError:
            old = {}
        old[nm] = r
        c.save_json(old, c.W + "/out/n6_meas.json")
        ru, kk = r["rudder"], r["keel"]
        print("%-14s ror bunn %.0f (min %.0f) TE x(-600) %.0f helning %.3f | trinn z %.0f x %s | kjol e_bunn %+.0f "
              "e_liste %+.0f dybde %.0f (modell %.0f) e_TE %+.0f | vindu x %s | hjoerne %.1f/%.1f px" % (
                  nm, ru["bot_z_mean"], ru["bot_z_min"], ru["te_x_at"]["-600.0"], ru["te_dxdz"], ru["step_z_mean"],
                  np.round(ru["step_x_range"]).tolist(), kk["e_bot_mm"], kk["e_strake_mm"], kk["depth_photo"],
                  kk["depth_model"], kk["e_te_mm"], np.round(r["window"]["pts"][:, 0]).tolist(),
                  r["corner"]["upper_px"], r["corner"]["lower_px"]), flush=True)
        print("   stripe z side %.0f ror %.0f | vindu px (modell-foto) %s | hjoerne y/z %s mod %s" % (
            r["boottop"]["side_z"], r["boottop"]["rudder_z"], np.round(r["window"]["px_model_minus_photo"]).tolist(),
            np.round(r["corner"]["photo_yz"][::3]).tolist(), np.round(r["corner"]["model_y_at_photo_z"][::3]).tolist()))
        print("   ror: TE x %s LE-lav x %s, trinn x %s, bunn x %s" % (
            {k: round(v) for k, v in r["rudder"]["te_x_at"].items()}, {k: round(v) for k, v in r["rudder"]["le_low_x_at"].items()},
            np.round(r["rudder"]["step_x_range"]).tolist(), np.round(r["rudder"]["bot_x_range"]).tolist()))
        print("   akter:", [(b["x0"], round(b["d_cl"]), None if b["d_sil"] is None else round(b["d_sil"]),
                             round(b["d_px_mm"])) for b in r["aft"]], flush=True)

