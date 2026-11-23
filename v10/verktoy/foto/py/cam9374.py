"""Kamera for IMG_9374 (babord side, baaten i stroppene, 761 x 472), loest bare
fra trekk som trinn 5 (forkroppen under vann) ikke endrer:

  strake   fenderlistens senter langs hele siden (x >= 60, stevnen krysser listen ved x ~ 40)
  stem     stevnens forkant over z ~ +300 (rett linje P.STEM_LINE)
  window   vinduets for- og akterende (ytre ramme), +-4 px (~ +-50 mm)
  keel_le  kjolens forkant (silhuett) under z ~ -650, keel_bot bunnen,
  keel_te  bakkanten (A._KeelProfile, 240 mm tykk, fas i bunnen)
  bt_top   vannlinjestripens blaa overkant og
  bt_red   lys stripe -> roedt, bare aktenfor x ~ 3 800 (der siden er
           loddrett og trinn 5 ikke rokker); hoeyden fri (som cam9387.py)

Forkroppens omriss under vann og stripen forut brukes IKKE. Roret (det roede
bladet ved u 674-686) og skrogets omriss akter for kjolen er kontroller.

Bildet er et utsnitt med ukjent brennvidde og ukjent hovedpunkt; f er fri
(svak prior 1000 +- 600 px), hovedpunktet er bildets midte (et forskjoevet
hovedpunkt tas nesten helt opp av giring/stamping).

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python cam9374.py
"""
import json
import math
import time

import numpy as np
from scipy.optimize import least_squares

import common as c
import uwlib as U
import geo9374 as G

G.use_model()            # modellen fra commit G.MODEL_REV (foer trinn 5), se geo9374.use_model
P, C = c.P, c.C
W_, H_ = 761, 472
T = json.load(open(c.W + "/out/t9374_cam.json"))


Cam9374 = G.Cam9374


# kameramodeller: hvilke ekstra parametre er frie (etter de 7 i uwlib.Cam)
CAMX = {"pin": [], "pp": ["du", "dv"], "k1": ["k1"], "ppk1": ["du", "dv", "k1"], "asp": ["asp"],
        "ppasp": ["du", "dv", "asp"], "k1asp": ["k1", "asp"]}
CMODE = {"m": "pin"}


def ncam(mode=None):
    return 7 + len(CAMX[mode or CMODE["m"]])


def make_cam(q, mode=None):
    mode = mode or CMODE["m"]
    kw = dict(zip(CAMX[mode], q[7:7 + len(CAMX[mode])]))
    return Cam9374(q[:7], W_, H_, **kw)


def arr(k):
    return np.asarray(T[k], float)


# ---------------------------------------------------------------- 3D-trekk
STRAKE3 = G.strake3(60.0, None, 360)
BT_X0 = 3800.0
STEM3 = G.stem_top3(260.0, 1100.0, 60)
WIN3 = G.window_ends()
VK, FK = G.keel_mesh()
VR, FR = G.rudder_mesh()

# ---------------------------------------------------------------- observasjoner
OBS = {}
st = arr("strake")
OBS["strake"] = st[:, [0, 3]]
sm = arr("stem")
OBS["stem_all"] = sm
bt = arr("boottop")
OBS["bt_top"] = bt[np.isfinite(bt[:, 1])][:, [0, 1]]
OBS["bt_red"] = bt[np.isfinite(bt[:, 4])][:, [0, 4]]
w = T["window"]
OBS["window"] = np.array([w["fwd_end"], w["aft_end"]], float)
kle = arr("keel_le"); OBS["keel_le"] = kle[(kle[:, 0] >= 352) & (kle[:, 0] <= 404)]
kte = arr("keel_te"); OBS["keel_te"] = kte[(kte[:, 0] >= 356) & (kte[:, 0] <= 396)]
kbo = arr("keel_bot"); OBS["keel_bot"] = kbo[(kbo[:, 0] >= 488) & (kbo[:, 0] <= 574)]
OBS["rudder"] = arr("rudder")
for _k in ("keel_le", "keel_te", "keel_bot"):       # uwlib.row_extents krever jevnt fordelte rader/kolonner
    assert np.allclose(np.diff(OBS[_k][:, 0]), 1.0), "hull i %s - bruk et jevnt rutenett" % _k

SIG = dict(strake=1.0, stem=1.0, window=4.0, keel_le=1.5, keel_te=1.5, keel_bot=1.5, bt_top=1.0, bt_red=1.0)
SEL = {"stem_v": (125.0, 225.0), "u_bt": 470.0}


def curve_resid(cam, X3, obs, along="u", cap=20.0):
    u, v, z = cam.project(X3)
    ok = z > 100
    u, v = u[ok], v[ok]
    if len(u) < 2:
        return np.full(len(obs), cap)
    if along == "u":
        o = np.argsort(u); uu, vv = u[o], v[o]
        inside = (obs[:, 0] > uu[0]) & (obs[:, 0] < uu[-1])
        pred = np.interp(obs[:, 0], uu, vv)
        return np.where(inside, pred - obs[:, 1], cap)
    o = np.argsort(v); uu, vv = u[o], v[o]
    inside = (obs[:, 0] > vv[0]) & (obs[:, 0] < vv[-1])
    pred = np.interp(obs[:, 0], vv, uu)
    return np.where(inside, pred - obs[:, 1], cap)


# stripens to kanter aktenfor BT_X0, beregnet EN gang i nominell hoeyde + 100 mm
# (siden er nesten loddrett der, saa en hoeydeendring flytter linja bare i z)
BT_BASE = G.zline3(lambda x: G.bt_top_z(x) + 100.0, BT_X0, P.LOA, 90)
BR_BASE = G.zline3(lambda x: 138.0 + 0.0 * x, BT_X0, P.LOA, 90)
BT_UMAX = 645.0          # bakre stropp og liften aktenfor


def bt_lines(dt, dr, k):
    a = BT_BASE.copy(); a[:, 2] += (dt - 100.0) + k * (a[:, 0] - 4000.0) / 1000.0
    b = BR_BASE.copy(); b[:, 2] += (dr - 100.0) + k * (b[:, 0] - 4000.0) / 1000.0
    return a, b


def stem_obs():
    o = OBS["stem_all"]
    a, b = SEL["stem_v"]
    return o[(o[:, 0] >= a) & (o[:, 0] <= b)]


def residuals(q, parts=False, use_bt=True, f0=1000.0, fs=600.0):
    p = q[:7]
    cam = make_cam(q)
    nb = ncam()
    g = {}
    g["strake"] = curve_resid(cam, STRAKE3, OBS["strake"])
    g["stem"] = curve_resid(cam, STEM3, stem_obs(), along="v")
    u, v, _ = cam.project(WIN3)
    g["window"] = np.r_[u - OBS["window"][:, 0], v - OBS["window"][:, 1]]
    o = OBS["keel_le"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0])
    g["keel_le"] = np.where(np.isfinite(lo), lo - o[:, 1], 20.0)
    o = OBS["keel_te"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0])
    g["keel_te"] = np.where(np.isfinite(hi), hi - o[:, 1], 20.0)
    o = OBS["keel_bot"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0], axis="col")
    g["keel_bot"] = np.where(np.isfinite(hi), hi - o[:, 1], 20.0)
    if use_bt:
        BT, BR = bt_lines(float(q[nb]), float(q[nb + 1]), float(q[nb + 2]))
        ub = SEL["u_bt"]
        o = OBS["bt_top"]; o = o[(o[:, 0] >= ub) & (o[:, 0] <= BT_UMAX)]
        g["bt_top"] = curve_resid(cam, BT, o)
        o = OBS["bt_red"]; o = o[(o[:, 0] >= ub) & (o[:, 0] <= BT_UMAX)]
        g["bt_red"] = curve_resid(cam, BR, o)
    g["prior"] = np.array([(p[6] - f0) / fs])
    if parts:
        return g
    out = []
    for k, r in g.items():
        if k == "prior":
            out.append(r)
        else:
            out.append(r / SIG[k] / np.sqrt(max(len(r), 1) / 20.0))
    return np.concatenate(out)


def rms(v):
    return float(np.sqrt(np.mean(np.square(v)))) if len(v) else float("nan")


def look_angles(Cpos, target):
    d = np.asarray(target, float) - np.asarray(Cpos, float)
    yaw = math.degrees(math.atan2(d[1], d[0]))
    pitch = math.degrees(math.atan2(-d[2], math.hypot(d[0], d[1])))
    return yaw, pitch


XS7 = [100, 100, 50, 0.5, 0.5, 0.5, 30]
LB7 = [-np.inf] * 6 + [200.0]
UB7 = [np.inf] * 6 + [6000.0]
XSX = dict(du=10.0, dv=10.0, k1=0.05, asp=0.02)
LBX = dict(du=-250.0, dv=-250.0, k1=-0.6, asp=0.6)
UBX = dict(du=250.0, dv=250.0, k1=0.6, asp=1.6)
X0X = dict(du=0.0, dv=0.0, k1=0.0, asp=1.0)
XSB, LBB, UBB = [20, 20, 5], [-250.0, -250.0, -60.0], [400.0, 400.0, 60.0]


def bounds(use_bt):
    ex = CAMX[CMODE["m"]]
    xs = XS7 + [XSX[k] for k in ex] + (XSB if use_bt else [])
    lb = LB7 + [LBX[k] for k in ex] + (LBB if use_bt else [])
    ub = UB7 + [UBX[k] for k in ex] + (UBB if use_bt else [])
    return np.array(xs), np.array(lb), np.array(ub)


def pad(s, use_bt, bt0=(100.0, 100.0, 0.0)):
    """Startvektor for gjeldende modus fra en vilkaarlig startvektor s =
    7 kamera [+ ekstra] [+ stripe]; manglende ekstra = 0, stripe = bt0."""
    s = list(s)
    names = CAMX[CMODE["m"]]
    ne = len(names)
    ex = s[7:7 + ne] if len(s) >= 7 + ne else []
    ex = ex + [X0X[k] for k in names[len(ex):]]
    out = s[:7] + ex
    if use_bt:
        bt = s[7 + ne:7 + ne + 3] if len(s) >= 7 + ne + 3 else list(bt0)
        out += list(bt)
    return np.array(out, float)


def solve(starts, use_bt=True, nfev=600):
    xs, lb, ub = bounds(use_bt)
    best = None
    for s in starts:
        s = np.clip(s, lb + 1e-9, ub - 1e-9)
        try:
            r = least_squares(lambda q: residuals(q, use_bt=use_bt), s, x_scale=xs, loss="soft_l1",
                              f_scale=2.0, max_nfev=nfev, bounds=(lb, ub), diff_step=1e-5)
        except Exception as e:          # noqa
            print("  start feilet:", e)
            continue
        if best is None or r.cost < best.cost:
            best = r
    return best


def uncertainty(r):
    J = r.jac
    dof = max(len(r.fun) - len(r.x), 1)
    s2 = float(np.sum(r.fun ** 2) / dof)
    try:
        return np.sqrt(np.diag(np.linalg.inv(J.T @ J) * s2))
    except np.linalg.LinAlgError:
        return np.full(len(r.x), np.nan)


def update_selection(q):
    """Stevnens rader: z mellom 300 og 1080 paa stevnlinja; stripens kolonner:
    aktenfor x = BT_X0 paa skrogsiden."""
    cam = make_cam(q)
    zz = np.array([300.0, 1080.0])
    (xa, za), (xb, zb) = P.STEM_LINE
    xx = xa + (zz - za) * (xb - xa) / (zb - za)
    _, v, _ = cam.project(np.c_[xx, 0 * zz, zz])
    SEL["stem_v"] = (float(min(v)) + 1.0, float(max(v)) - 1.0)
    X = G.zline3(lambda x: 100.0, BT_X0, BT_X0 + 1.0, 2)
    u, _, _ = cam.project(X[:1])
    SEL["u_bt"] = float(u[0]) + 6.0


def summarize(r, use_bt):
    g = residuals(r.x, True, use_bt=use_bt)
    return dict(q=r.x, p=r.x[:7], extra=dict(zip(CAMX[CMODE["m"]], r.x[7:ncam()])), sd=uncertainty(r),
                rms={k: rms(v) for k, v in g.items()}, mean={k: float(np.mean(v)) for k, v in g.items()},
                n={k: len(v) for k, v in g.items()}, cost=float(r.cost), sel=dict(SEL), cmode=CMODE["m"],
                use_bt=use_bt)


def show(tag, d):
    nl = chr(10) + "   "
    print(tag, np.round(d["q"], 3).tolist(), nl + "sd", np.round(d["sd"], 3).tolist(),
          nl + "rms", {k: round(v, 2) for k, v in d["rms"].items()},
          nl + "mean", {k: round(v, 2) for k, v in d["mean"].items()}, "cost %.1f" % d["cost"], flush=True)


if __name__ == "__main__":
    t0 = time.time()
    CMODE["m"] = "pin"
    starts = []
    for cx in (500.0, 2000.0, 3500.0):
        for cy in (-5000.0, -8000.0, -12000.0):
            for f in (700.0, 1100.0):
                Cp = (cx, cy, 150.0)
                yaw, pitch = look_angles(Cp, (3500.0, 0.0, -100.0))
                starts.append([cx, cy, 150.0, yaw, pitch, 0.0, f])
    res = []
    for s in starts:
        r = solve([pad(s, False)], use_bt=False, nfev=150)
        if r is not None:
            res.append(r)
    res.sort(key=lambda r: r.cost)
    print("grov: beste kost", [round(r.cost, 1) for r in res[:5]], "%.0fs" % (time.time() - t0), flush=True)
    r = solve([res[0].x, res[1].x, res[2].x], use_bt=False, nfev=800)
    update_selection(r.x)
    base = r.x[:7]
    out = {}
    for cm in ("pin", "pp", "k1", "ppk1", "asp", "ppasp", "k1asp"):
        CMODE["m"] = cm
        for use_bt in (False, True):
            tag = cm + ("_bt" if use_bt else "")
            st = [pad(base, use_bt)] + [pad(out[t]["q"][:7], use_bt) for t in out if not t.endswith("_bt")]
            if use_bt and cm in out:
                st.append(pad(out[cm]["q"], use_bt))
            r = solve(st, use_bt=use_bt, nfev=1000)
            update_selection(r.x)
            r = solve([r.x], use_bt=use_bt, nfev=1000)
            out[tag] = summarize(r, use_bt)
            show(tag, out[tag])
    main = "k1_bt"          # se notatet i e9374.py om valget
    q = out[main]["q"]
    CMODE["m"] = out[main]["cmode"]
    nb = ncam()
    resj = dict(p=q[:7], keys=["Cx", "Cy", "Cz", "yaw", "pitch", "roll", "f"], W=W_, H=H_, main=main,
                extra=out[main]["extra"], bt_dz_top=float(q[nb]), bt_dz_red=float(q[nb + 1]),
                bt_slope_per_m=float(q[nb + 2]), bt_x0=BT_X0, sel=out[main]["sel"], modes=out,
                note=("Hovedkamera = modes[main]: uwlib.Cam(p, 761, 472) naar main er 'pin_bt'. Stripens hoeyde fri "
                      "aktenfor x 3800 (blaa overkant z = bt_top_z(x) + bt_dz_top + k (x-4000)/1000, roedt fra "
                      "z = 38 + bt_dz_red + k (x-4000)/1000). Andre moduser: pp = fritt hovedpunkt (du, dv), "
                      "k1 = radial fortegning, _bt = med stripen. Se cam9374.py."))
    c.save_json(resj, c.W + "/out/cam9374.json")
    print("ferdig %.0fs" % (time.time() - t0))
