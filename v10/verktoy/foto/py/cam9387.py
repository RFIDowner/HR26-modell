"""Kamera for IMG_9387 (babord side paa land, 2000 x 1500), loest bare fra
trekk som trinn 5 (forkroppen under vann) ikke endrer:

  strake   fenderlistens senter langs hele siden
  bt_top   vannlinjestripens blaa overkant, bare aktenfor x ~ 3 800 (der
           siden er loddrett og trinn 5 ikke rokker); hoeyden FRI (se under)
  bt_red   lys stripe -> roedt, samme utvalg, hoeyden FRI
  window   vinduets for- og akterende (ytre ramme), svak vekt (+-100 mm)
  keel_le  kjolens forkant (silhuett) under z ~ -700, keel_bot bunnen,
  keel_te  bakkanten (A._KeelProfile, 240 mm tykk, fas)
  rud_te   rorets bakkant (silhuett), rud_bot bunnen
  transom  akterspeilets hjoerne (skrogets hoeyre silhuett, rad 500-550, 592-604)
  stem     stevnen over z ~ +300 (rett linje P.STEM_LINE), rad 476-512

Forkroppens omriss under vann og stripen forut brukes IKKE.

Hoeydene fra IMG_9370 (roedt fra z +38, blaa overkant 146 -> 125) passer
ikke med fenderlisten, stevnen og kjolen i dette bildet: med dem laast blir
listen skjev (+-15 px) og stripen forut 50 px feil. Fenderlisten, stevnen og
kjolen alene passer innen 1-3 px, og da ligger stripen ca. 100 mm hoeyere
(samme funn som IMG_9391 'liste' i cam9391e.py: 233/152). Hovedkameraet
('fri') lar derfor stripens hoeyde vaere fri: z = z0 + dz + k * (x - 4000)/1000,
felles helning k for begge kanter. 'bt38' (hoeydene laast) og 'utenbt' (uten
stripe) lagres til sammenligning.
Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python cam9387.py
"""
import json
import sys
import time

import numpy as np
from scipy.optimize import least_squares

import common as c
import uwlib as U
import geo9387 as G

P, C = c.P, c.C
W_, H_ = 2000, 1500
T = json.load(open(c.W + "/out/t9387_cam.json"))


def arr(k):
    return np.asarray(T[k], float)


# ---------------------------------------------------------------- 3D-trekk
STRAKE3 = G.strake3(450.0, None, 320)
BT_X0 = 3800.0
BTTOP3 = G.zline3(G.bt_top_z, BT_X0, P.LOA, 160)
BTRED3 = G.zline3(lambda x: 38.0, BT_X0, P.LOA, 160)
WIN3 = G.window_ends()
STEM3 = G.stem_top3(260.0, 700.0, 40)
VK, FK = G.keel_mesh()
VR, FR = G.rudder_mesh()
VH, FH = U.hull_mesh(200, 50)

# ---------------------------------------------------------------- observasjoner
st = arr("strake")
OBS = {}
OBS["strake"] = st[:, [0, 3]]
bt = arr("boottop")
OBS["bt_top"] = bt[np.isfinite(bt[:, 1])][:, [0, 1]]
OBS["bt_red"] = bt[np.isfinite(bt[:, 4])][:, [0, 4]]
w = T["window"]
OBS["window"] = np.array([w["fwd_end"], w["aft_end"]], float)
kle = arr("keel_le"); OBS["keel_le"] = kle[(kle[:, 0] >= 850) & (kle[:, 0] <= 990)]
kte = arr("keel_te"); OBS["keel_te"] = kte[(kte[:, 0] >= 840) & (kte[:, 0] <= 955)]
kbo = arr("keel_bot"); OBS["keel_bot"] = kbo[((kbo[:, 0] >= 1120) & (kbo[:, 0] <= 1160)) |
                                             ((kbo[:, 0] >= 1250) & (kbo[:, 0] <= 1370))]
rte = arr("rudder_te"); OBS["rud_te"] = rte[(rte[:, 0] >= 700) & (rte[:, 0] <= 815)]
rbo = arr("rudder_bot"); OBS["rud_bot"] = rbo[(rbo[:, 0] >= 1632) & (rbo[:, 0] <= 1660)]
tr = arr("transom"); OBS["transom"] = tr[((tr[:, 0] >= 500) & (tr[:, 0] <= 550)) | ((tr[:, 0] >= 592) & (tr[:, 0] <= 604))]
sm = arr("stem_top"); OBS["stem"] = sm[(sm[:, 0] >= 476) & (sm[:, 0] <= 512)][:, :2]

SIG = dict(strake=1.5, bt_top=1.5, bt_red=1.5, window=30.0, keel_le=2.0, keel_te=2.0, keel_bot=3.0,
           rud_te=3.0, rud_bot=5.0, transom=4.0, stem=3.0)
MODES = dict(fri=dict(bt=True, free=True), bt38=dict(bt=True, free=False), utenbt=dict(bt=False, free=False))


def curve_resid(cam, X3, obs, along="u"):
    u, v, z = cam.project(X3)
    ok = z > 100
    u, v = u[ok], v[ok]
    if len(u) < 2:
        return np.full(len(obs), 30.0)
    if along == "u":
        o = np.argsort(u); uu, vv = u[o], v[o]
        inside = (obs[:, 0] > uu[0]) & (obs[:, 0] < uu[-1])
        pred = np.interp(obs[:, 0], uu, vv)
        return np.where(inside, pred - obs[:, 1], 30.0)
    o = np.argsort(v); uu, vv = u[o], v[o]
    inside = (obs[:, 0] > vv[0]) & (obs[:, 0] < vv[-1])
    pred = np.interp(obs[:, 0], vv, uu)
    return np.where(inside, pred - obs[:, 1], 30.0)


def bt_select(cam):
    """u-grensen for stripens utvalg (x >= BT_X0) med dette kameraet."""
    u, v, _ = cam.project(BTTOP3[:1])
    return float(u[0])


def make_cam(p):
    return U.Cam(p[:7], W_, H_)


U_BT = None
_LINES = {}


def bt_lines(dt, dr, k):
    """Stripens to kanter paa skrogsiden aktenfor BT_X0 med hoeyde-forskyvning
    dt (blaa overkant), dr (roedt) og felles helning k mm per m."""
    key = (dt, dr, k)
    L = _LINES.get(key)
    if L is None:
        zt = lambda x: G.bt_top_z(x) + dt + k * (x - 4000.0) / 1000.0
        zr = lambda x: 38.0 + dr + k * (x - 4000.0) / 1000.0
        L = (G.zline3(zt, BT_X0, P.LOA, 120), G.zline3(zr, BT_X0, P.LOA, 120))
        if len(_LINES) > 2000:
            _LINES.clear()
        _LINES[key] = L
    return L


def residuals(q, parts=False, mode="fri", f0=1490.0, fs=40.0):
    """q = 7 kamera (+ dz_top, dz_red, k for stripen i 'fri')."""
    m = MODES[mode]
    p = q[:7]
    cam = make_cam(p)
    g = {}
    g["strake"] = curve_resid(cam, STRAKE3, OBS["strake"])
    if m["bt"]:
        ub = U_BT if U_BT is not None else bt_select(cam)
        if m["free"]:
            BT, BR = bt_lines(float(q[7]), float(q[8]), float(q[9]))
        else:
            BT, BR = BTTOP3, BTRED3
        o = OBS["bt_top"]; o = o[o[:, 0] >= ub + 5]
        g["bt_top"] = curve_resid(cam, BT, o)
        o = OBS["bt_red"]; o = o[o[:, 0] >= ub + 5]
        g["bt_red"] = curve_resid(cam, BR, o)
    u, v, _ = cam.project(WIN3)
    g["window"] = np.r_[u - OBS["window"][:, 0], v - OBS["window"][:, 1]]
    o = OBS["keel_le"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0])
    g["keel_le"] = np.where(np.isfinite(lo), lo - o[:, 1], 30.0)
    o = OBS["keel_te"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0])
    g["keel_te"] = np.where(np.isfinite(hi), hi - o[:, 1], 30.0)
    o = OBS["keel_bot"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0], axis="col")
    g["keel_bot"] = np.where(np.isfinite(hi), hi - o[:, 1], 30.0)
    o = OBS["rud_te"]; lo, hi = U.row_extents(cam, VR, FR, o[:, 0])
    g["rud_te"] = np.where(np.isfinite(hi), hi - o[:, 1], 30.0)
    o = OBS["rud_bot"]; lo, hi = U.row_extents(cam, VR, FR, o[:, 0], axis="col")
    g["rud_bot"] = np.where(np.isfinite(hi), hi - o[:, 1], 30.0)
    o = OBS["transom"]; lo, hi = U.row_extents(cam, VH, FH, o[:, 0])
    g["transom"] = np.where(np.isfinite(hi), hi - o[:, 1], 30.0)
    g["stem"] = curve_resid(cam, STEM3, OBS["stem"], along="v")
    g["prior"] = np.array([(p[6] - f0) / fs])
    if parts:
        return g
    out = []
    for k, v in g.items():
        if k == "prior":
            out.append(v * 3.0)
        else:
            out.append(v / SIG[k] / np.sqrt(max(len(v), 1) / 20.0))
    return np.concatenate(out)


def rms(v):
    return float(np.sqrt(np.mean(np.square(v)))) if len(v) else float("nan")


# ---------------------------------------------------------------- startverdi fra haandpunkter
def landmarks():
    k = G.keel_outline_xz()
    lm3 = [
        (P.RUDDER_TE_X, 0.0, P.RUDDER_BOT_Z),        # rorets bakkant nederst
        (5705.0, -100.0, -1390.0),                    # kjolens bakkant nederst
        (4400.0, -100.0, -1395.0),                    # kjolbunnen der hjoernebuen slutter
        tuple(WIN3[0]), tuple(WIN3[1]),
        tuple(STEM3[0]),                              # stevnen, z 260
        tuple(STRAKE3[-1]),                           # listen ved akterspeilet
    ]
    lm2 = [(1668, 828), (1392, 972), (1215, 1022), tuple(OBS["window"][0]), tuple(OBS["window"][1]),
           (60, 520), (1815, 488)]
    return np.array(lm3), np.array(lm2, float)


def lm_resid(p, X, x):
    cam = U.Cam(p[:7], W_, H_)
    u, v, _ = cam.project(X)
    return np.r_[u - x[:, 0], v - x[:, 1], (p[6] - 1490.0) / 20.0]


XS = [100, 100, 50, 0.5, 0.5, 0.5, 30, 20, 20, 5]


def solve(mode, starts):
    npar = 10 if MODES[mode]["free"] else 7
    lb = [-np.inf] * 7 + [-250.0, -250.0, -60.0]
    ub = [np.inf] * 7 + [400.0, 400.0, 60.0]
    best = None
    for s in starts:
        s = list(s[:7]) + list(s[7:npar]) + [100.0, 100.0, 0.0][len(s[7:npar]):npar - 7]
        r = least_squares(lambda q: residuals(q, mode=mode), s, x_scale=XS[:npar], loss="soft_l1", f_scale=2.0,
                          max_nfev=500, bounds=(lb[:npar], ub[:npar]), diff_step=1e-5)
        if best is None or r.cost < best.cost:
            best = r
    return best


def uncertainty(r):
    """1-sigma fra Jacobi ved loesningen, skalert med restene (lineaer)."""
    J = r.jac
    dof = max(len(r.fun) - len(r.x), 1)
    s2 = float(np.sum(r.fun ** 2) / dof)
    try:
        return np.sqrt(np.diag(np.linalg.inv(J.T @ J) * s2))
    except np.linalg.LinAlgError:
        return np.full(len(r.x), np.nan)


if __name__ == "__main__":
    X, x = landmarks()
    best = None
    for cx in (1500.0, 2500.0, 3500.0):
        for cy in (-3000.0, -4500.0, -6000.0):
            for yaw in (60.0, 75.0, 90.0):
                s = [cx, cy, 100.0, yaw, 0.0, 0.0, 1490.0]
                r = least_squares(lm_resid, s, args=(X, x), x_scale=[200, 200, 100, 1, 1, 1, 50], max_nfev=400)
                if best is None or r.cost < best.cost:
                    best = r
    p0 = best.x
    print("haandpunkter:", np.round(p0, 2).tolist(), "rms %.1f px" % rms(lm_resid(p0, X, x)[:-1]), flush=True)
    U_BT = bt_select(U.Cam(p0, W_, H_))
    starts = [p0, [323.0, -3847.0, 124.0, 51.3, 5.1, -0.6, 1436.0], [265.0, -4055.0, -103.0, 51.6, 2.8, 1.6, 1476.0],
              [612.0, -4840.0, 103.0, 58.1, 6.8, -3.0, 1458.0]]
    out = {}
    for mode in ("fri", "bt38", "utenbt"):
        t0 = time.time()
        r = solve(mode, starts)
        U_BT = bt_select(U.Cam(r.x[:7], W_, H_))
        r = solve(mode, [r.x])
        g = residuals(r.x, True, mode)
        sd = uncertainty(r)
        out[mode] = dict(q=r.x, p=r.x[:7], sd=sd, rms={k: rms(v) for k, v in g.items()},
                         mean={k: float(np.mean(v)) for k, v in g.items()}, n={k: len(v) for k, v in g.items()},
                         u_bt_min=U_BT, cost=float(r.cost))
        print(mode, np.round(r.x, 2).tolist(), "sd", np.round(sd, 2).tolist(), "%.0fs" % (time.time() - t0))
        print("   rms", {k: round(rms(v), 2) for k, v in g.items()}, flush=True)
    q = out["fri"]["q"]
    res = dict(p=out["fri"]["p"], keys=["Cx", "Cy", "Cz", "yaw", "pitch", "roll", "f"], W=W_, H=H_,
               bt_dz_top=float(q[7]), bt_dz_red=float(q[8]), bt_slope_per_m=float(q[9]),
               bt_x0=BT_X0, modes=out,
               note=("uwlib.Cam(p, 2000, 1500). Hovedkamera 'fri': stripens hoeyde fri. Stripen i dette kameraet: "
                     "blaa overkant z = bt_top_z(x) + bt_dz_top + k (x-4000)/1000, roedt fra z = 38 + bt_dz_red + "
                     "k (x-4000)/1000. Se cam9387.py."))
    c.save_json(res, c.W + "/out/cam9387.json")
