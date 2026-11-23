"""Kamera for «nye (6).jpeg» (styrbord laaring, lavt kamera, 1170 x 1588),
loest bare fra trekk som spoersmaalene ikke gjelder:

  strake     fenderlistens senter paa styrbord side (u 262-1087), fortsatt
             rundt hjoernet inn paa akterspeilet (hull._strake_path), sigma 1 px
  strake_tr  listen paa akterspeilets babord halvdel (u 100-141), med
             buen 42 mm opp mot midten (P.STRAKE_TRANSOM_RISE), sigma 1,5 px
  far_end    listens ende ved babord akterspeilhjoerne, sigma 3 px
  (bt)       vannlinjestripens blaa overkant paa siden, hoeyde og helning
             FRIE (stripen paa land er ikke et hoeydeanker), sigma 1 px
  (keel)     kjolens forkant, bakkant og bunn - bare i variantene *_keel,
             for aa se hvor mye svaret paa spoersmaal 3 haenger paa kjolen

Kameramodeller: pin (hullkamera, hovedpunkt i bildets midte), k1 (radial
fortegning), pp (fritt hovedpunkt), ppk1. Spredningen mellom variantene er
usikkerheten i maalene (n6_meas.py).

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 --lock -- python n6_cam.py
"""
import json
import math
import sys
import time

import numpy as np
from scipy.optimize import least_squares

import common as c
import uwlib as U
import n6_geo as N
import geo9374 as G

P, C = N.P, N.C
T = json.load(open(c.W + "/out/n6_trace.json"))
W_, H_ = T["W"], T["H"]

CAMX = {"pin": [], "k1": ["k1"], "pp": ["du", "dv"], "ppk1": ["du", "dv", "k1"], "k12": ["k1", "k2"],
        "ppk12": ["du", "dv", "k1", "k2"], "asp": ["asp"], "ppasp": ["du", "dv", "asp"], "k1asp": ["k1", "asp"]}
XSX = dict(du=10.0, dv=10.0, k1=0.05, k2=0.05, asp=0.02)
LBX = dict(du=-300.0, dv=-400.0, k1=-1.5, k2=-3.0, asp=0.6)
UBX = dict(du=300.0, dv=400.0, k1=1.5, k2=3.0, asp=1.6)
X0X = dict(du=0.0, dv=0.0, k1=0.0, k2=0.0, asp=1.0)

S3 = N.strake_paths()
NEAR3 = np.vstack([S3["side"], S3["tr_stbd"]])        # styrbord side + akterspeilet til senterlinjen
FAR3 = S3["tr_port"]                                  # akterspeilets babord halvdel
FAR_END3 = S3["corner_port"][None, :]
VK, FK = N.keel_mesh()

OBS = {}
st = np.asarray(T["strake"], float)
OBS["strake"] = st[st[:, 0] >= 262][:, [0, 3]]     # u < 262: gummiens ende og staalbeslaget ved roret
OBS["strake_tr"] = np.asarray(T["strake_tr"], float)[:, [0, 3]]
OBS["far_end"] = np.array([T["corner"]["far_end"]], float)
bt = np.asarray(T["boottop"], float)
bt = bt[np.isfinite(bt[:, 1]) & (bt[:, 0] >= 262) & (bt[:, 0] <= 1070)]
bt = bt[(bt[:, 0] < 862) | (bt[:, 0] > 905)]          # bakre stropp krysser stripen
OBS["bt"] = bt[::2][:, [0, 1]]
kle = np.asarray(T["keel_le"], float); OBS["keel_le"] = kle[(kle[:, 0] >= 1110) & (kle[:, 0] <= 1235)]
kte = np.asarray(T["keel_te"], float); OBS["keel_te"] = kte[(kte[:, 0] >= 1135) & (kte[:, 0] <= 1268)]
kbo = np.asarray(T["keel_bot"], float); OBS["keel_bot"] = kbo[(kbo[:, 0] >= 632) & (kbo[:, 0] <= 760)]
OBS["corner"] = np.asarray(T["tr_corner"], float)[:, :2]
CORNER3 = N.transom_corner_line(60.0, None, 80)

SIG = dict(strake=1.0, strake_tr=1.5, far_end=3.0, bt=1.0, keel_le=1.5, keel_te=1.5, keel_bot=1.5, corner=1.5)


def poly_dist(cam, X3, obs, cap=25.0):
    """Fortegnsavstand (px) fra hvert observert punkt til den projiserte
    polylinja (normal mot hoeyre/ned positiv)."""
    u, v, z = cam.project(X3)
    ok = z > 100
    Q = np.c_[u[ok], v[ok]]
    if len(Q) < 2:
        return np.full(len(obs), cap)
    a, b = Q[:-1], Q[1:]
    ab = b - a
    L2 = np.maximum((ab ** 2).sum(1), 1e-9)
    t = np.clip(((obs[:, None, :] - a[None]) * ab[None]).sum(2) / L2[None], 0.0, 1.0)
    proj = a[None] + t[..., None] * ab[None]
    d2 = ((obs[:, None, :] - proj) ** 2).sum(2)
    j = np.argmin(d2, axis=1)
    dv = obs - proj[np.arange(len(obs)), j]
    n = np.c_[-ab[j, 1], ab[j, 0]] / np.sqrt(L2[j])[:, None]
    n *= np.sign(n[:, 0] + n[:, 1] + 1e-12)[:, None]
    return np.clip((dv * n).sum(1), -cap, cap)


def make_cam(q, mode):
    kw = dict(zip(CAMX[mode], q[7:7 + len(CAMX[mode])]))
    return N.Cam(q[:7], W_, H_, **kw)


def curve_resid(cam, X3, obs, cap=25.0):
    u, v, z = cam.project(X3)
    ok = z > 100
    u, v = u[ok], v[ok]
    if len(u) < 2:
        return np.full(len(obs), cap)
    o = np.argsort(u)
    uu, vv = u[o], v[o]
    inside = (obs[:, 0] > uu[0]) & (obs[:, 0] < uu[-1])
    pred = np.interp(obs[:, 0], uu, vv)
    return np.where(inside, pred - obs[:, 1], cap)


def bt_line(z0, k):
    return np.array([(x, -y, z) for x, y, z in G.zline3(lambda x: z0 + k * (x - 6000.0) / 1000.0, 2500.0,
                                                          P.LOA, 120)])


def keel_parts(cam):
    g = {}
    o = OBS["keel_le"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0])
    g["keel_le"] = np.where(np.isfinite(hi), hi - o[:, 1], 25.0)
    o = OBS["keel_te"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0])
    g["keel_te"] = np.where(np.isfinite(lo), lo - o[:, 1], 25.0)
    o = OBS["keel_bot"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0], axis="col")
    g["keel_bot"] = np.where(np.isfinite(hi), hi - o[:, 1], 25.0)
    return g


def residuals(q, cfg, parts=False):
    mode = cfg["mode"]
    nc = 7 + len(CAMX[mode])
    cam = make_cam(q, mode)
    g = {}
    g["strake"] = curve_resid(cam, NEAR3, OBS["strake"])
    if cfg.get("tr", True):
        g["strake_tr"] = curve_resid(cam, FAR3, OBS["strake_tr"])
        u, v, _ = cam.project(FAR_END3)
        g["far_end"] = np.r_[u - OBS["far_end"][:, 0], v - OBS["far_end"][:, 1]]
    if cfg.get("corner", True):
        o = OBS["corner"]
        if cfg.get("corner") == "upper":
            o = o[o[:, 1] < 830.0]
        g["corner"] = poly_dist(cam, CORNER3, o)
    if cfg.get("bt"):
        z0, k = q[nc], q[nc + 1]
        g["bt"] = curve_resid(cam, bt_line(z0, k), OBS["bt"])
    if cfg.get("keel"):
        g.update(keel_parts(cam))
    g["prior"] = np.array([(q[6] - 1150.0) / 800.0])
    if parts:
        return g
    out = []
    for k_, r in g.items():
        if k_ == "prior":
            out.append(r)
        else:
            out.append(r / SIG[k_] / np.sqrt(max(len(r), 1) / 20.0))
    return np.concatenate(out)


XS7 = [100, 100, 50, 0.5, 0.5, 0.5, 30]
LB7 = [-np.inf] * 6 + [250.0]
UB7 = [np.inf] * 6 + [6000.0]


def bounds(cfg):
    ex = CAMX[cfg["mode"]]
    xs = XS7 + [XSX[k] for k in ex] + ([20.0, 5.0] if cfg.get("bt") else [])
    lb = LB7 + [LBX[k] for k in ex] + ([-200.0, -80.0] if cfg.get("bt") else [])
    ub = UB7 + [UBX[k] for k in ex] + ([600.0, 80.0] if cfg.get("bt") else [])
    return np.array(xs), np.array(lb), np.array(ub)


def pad(s, cfg):
    s = list(s[:7])
    s += [X0X[k] for k in CAMX[cfg["mode"]]]
    if cfg.get("bt"):
        s += [220.0, 0.0]
    return np.array(s, float)


def solve(starts, cfg, nfev=800):
    xs, lb, ub = bounds(cfg)
    best = None
    for s in starts:
        s = np.clip(np.asarray(s, float), lb + 1e-9, ub - 1e-9)
        try:
            r = least_squares(lambda q: residuals(q, cfg), s, x_scale=xs, loss="soft_l1", f_scale=2.0,
                              max_nfev=nfev, bounds=(lb, ub), diff_step=1e-5)
        except Exception as e:          # noqa
            print("  start feilet:", e)
            continue
        if best is None or r.cost < best.cost:
            best = r
    return best


def rms(v):
    return float(np.sqrt(np.mean(np.square(v)))) if len(v) else float("nan")


def look_angles(Cpos, target):
    d = np.asarray(target, float) - np.asarray(Cpos, float)
    return math.degrees(math.atan2(d[1], d[0])), math.degrees(math.atan2(-d[2], math.hypot(d[0], d[1])))


def summarize(r, cfg):
    g = residuals(r.x, cfg, True)
    nc = 7 + len(CAMX[cfg["mode"]])
    return dict(q=r.x, cfg=cfg, rms={k: rms(v) for k, v in g.items()}, mean={k: float(np.mean(v)) for k, v in g.items()},
                n={k: len(v) for k, v in g.items()}, cost=float(r.cost),
                extra=dict(zip(CAMX[cfg["mode"]], r.x[7:nc])),
                bt=(r.x[nc:nc + 2].tolist() if cfg.get("bt") else None))


def show(tag, d):
    q = d["q"]
    print("%-14s C=(%.0f, %.0f, %.0f) yaw %.2f pitch %.2f roll %.2f f %.0f %s bt %s | rms %s | cost %.1f" % (
        tag, q[0], q[1], q[2], q[3], q[4], q[5], q[6], {k: round(v, 3) for k, v in d["extra"].items()},
        None if d["bt"] is None else [round(v, 1) for v in d["bt"]],
        {k: round(v, 2) for k, v in d["rms"].items()}, d["cost"]), flush=True)


VARIANTS = {
    # med kjolen (forkant, bakkant, bunn) som anker: hovedfamilien
    "pin_keel": dict(mode="pin", keel=True, corner="upper", tr=False),
    "k1_keel": dict(mode="k1", keel=True, corner="upper", tr=False),
    "pp_keel": dict(mode="pp", keel=True, corner="upper", tr=False),
    "ppk1_keel": dict(mode="ppk1", keel=True, corner="upper", tr=False),
    # uten kjolen: hoeydeskalaen fra akterspeilets hjoerne (hele, modellens V fra trinn 4)
    "pin_cfull": dict(mode="pin", corner=True, tr=False),
    "k1_cfull": dict(mode="k1", corner=True, tr=False),
    "pp_cfull": dict(mode="pp", corner=True, tr=False),
    "pin_cfull_bt": dict(mode="pin", corner=True, tr=False, bt=True),
    # kontroll: med akterspeilets babord halvdel (listebit og hjoerne) i tillegg
    "pin_keel_tr": dict(mode="pin", keel=True, corner="upper", tr=True),
    # piksel-forhold fritt (skjermklipp kan vaere skalert ujevnt)
    "asp_keel_tr": dict(mode="asp", keel=True, corner="upper", tr=True),
    "ppasp_keel_tr": dict(mode="ppasp", keel=True, corner="upper", tr=True),
    "asp_keel": dict(mode="asp", keel=True, corner="upper", tr=False),
}
MAIN = "pin_keel"          # hullkamera; k1-variantene trenger k1 1,2-1,4 (urimelig sterk fortegning)
GRID = [(10900.0, 3700.0, 450.0, -141.6, -1.8, -5.0, 1450.0), (10500.0, 4000.0, 350.0, -134.0, -4.0, -5.0, 1600.0),
        (9500.0, 3100.0, 450.0, -133.0, -4.0, -4.6, 1250.0), (11600.0, 4000.0, 170.0, -145.0, -4.6, -2.5, 1650.0),
        (11000.0, 3800.0, 300.0, -142.0, -1.0, -1.0, 1300.0)]


if __name__ == "__main__":
    t0 = time.time()
    names = sys.argv[1:] or list(VARIANTS)
    try:
        out = json.load(open(c.W + "/out/n6_cam.json"))["modes"]
    except (OSError, KeyError):
        out = {}
    for nm in names:
        cfg = VARIANTS[nm]
        starts = [pad(g, cfg) for g in GRID]
        if nm in out:
            starts.append(np.asarray(out[nm]["q"], float))
        if "k1" in CAMX[cfg["mode"]]:
            i1 = 7 + CAMX[cfg["mode"]].index("k1")
            for k1 in (0.3, 0.9):
                s_ = pad(GRID[0], cfg); s_[i1] = k1; starts.append(s_)
        r = solve(starts, cfg, nfev=150)
        r = solve([r.x], cfg, nfev=1500)
        out[nm] = summarize(r, cfg)
        show(nm, out[nm])
        c.save_json(dict(W=W_, H=H_, keys=["Cx", "Cy", "Cz", "yaw", "pitch", "roll", "f"], main=MAIN, modes=out,
                         note="Se n6_cam.py. q = 7 kamera + ekstra (CAMX[mode]) + [z0, k] for stripen naar bt."),
                    c.W + "/out/n6_cam.json")
    print("ferdig %.0fs" % (time.time() - t0))
