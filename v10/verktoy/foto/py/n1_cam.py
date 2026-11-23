"""Kamera for «nye (1).jpeg» (akterfra og nedenfra, baaten i stroppene),
loest bare fra trekk spoersmaalene ikke gjelder:

  strake_port     fenderlistens moerke baand paa babord side (senter), sigma 3
  strake_port_in  baandets indre kant (listens underkant mot skrogsiden), sigma 3
  strake_port_tr  listen paa akterspeilet (babord del), buen 42 mm opp, sigma 3
  strake_stbd_in  styrbord: indre kant langs siden, sigma 3
  strake_stbd_tr  styrbord: listen ved hjoernet paa akterspeilet, sigma 4
  top             akterspeilets overkant (hvit mot himmel), sigma 2
  keel_l/r/bot    kjolens omriss (bunn -1 400), sigma 2.5
  (rudder)        rorets lyse kant som senterlinje - bare i varianten *_rud;
                  roret er vridd, saa det er svakt

Varianter (spredningen er usikkerheten):
  pin   hullkamera, hovedpunkt i midten      pp    fritt hovedpunkt
  k1    radial fortegning                    ppk1  begge
  *_lo  listens baand modellert 15 mm lavere (baandet ses nedenfra)
  *_nok uten kjolen (bare liste og overkant)
  *_corn med listens to hjoerner som punkter (sigma 4)
  ppk12 fritt hovedpunkt og radial k1, k2 (vidvinkel/fortegning)
  *_rtip test: rorets nederste punkt tvunget til z -1 047 paa hengsellinja
  *_kdz kjolen med fri hoeydeforskyvning (tester om kjolen sitter riktig mot listen)
  *_rud med roret (forkant/hengsellinje i y = 0), sigma 6

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python n1_cam.py [variant ...]
"""
import json
import sys
import time

import numpy as np
from scipy.optimize import least_squares

import common as c
import uwlib as U
import n1_geo as N

P, C = N.P, N.C
T = json.load(open(c.W + "/out/n1_trace.json"))
W_, H_ = T["W"], T["H"]

VK0, FK = N.keel_mesh()
VK = VK0


def strake_in(side, x0=4000.0, n=200):
    """Listens underkant mot skrogsiden (indre kant av baandet sett nedenfra)."""
    xe = N.strake_corner()[0]
    xs = np.linspace(x0, xe - 2.0, n)
    out = []
    for x in xs:
        z = C.strake_z(x) - 0.5 * P.STRAKE_H
        y = N.side_y(x, z)
        if np.isfinite(y):
            out.append((x, side * y, z))
    return np.array(out)


def model_feats(dz_band=0.0):
    F = {}
    sp = N.strake_side(-1.0); sp[:, 2] += dz_band
    F["strake_port"] = sp
    F["strake_port_in"] = strake_in(-1.0)
    tp = N.strake_transom(-1.0); tp[:, 2] += dz_band
    F["strake_port_tr"] = tp
    F["strake_stbd_in"] = strake_in(1.0)
    ts = N.strake_transom(1.0); ts[:, 2] += dz_band
    F["strake_stbd_tr"] = ts
    so = N.strake_side(-1.0, 2500.0, 250)
    so[:, 1] = [-(N.side_y(x, z) + P.STRAKE_PROUD) for x, z in zip(so[:, 0], so[:, 2])]
    F["strake_port_sil"] = so
    tt = N.transom_top(); tt[:, 2] -= 10.0
    F["top"] = tt
    F["rudder"] = N.rudder_le(-1000.0, 600.0)     # hengsellinja, y = 0 (forlenget opp langs akterspeilet)
    F["rudder"][:, 0] = [C.transom_x(z, 0.0) + 15.0 for z in F["rudder"][:, 2]]
    return F


def clean(name):
    a = np.asarray(T[name], float)
    if name in ("keel_l", "keel_r"):
        return a[:, [1, 0]]          # (u, v)
    return a[:, :2]


OBS = {k: clean(k) for k in ("strake_port", "strake_port_in", "strake_port_tr", "strake_stbd_in", "strake_stbd_tr",
                              "top", "keel_l", "keel_r", "keel_bot", "rudder")}
OBS["rudder"] = OBS["rudder"][(OBS["rudder"][:, 1] >= 1000) & (OBS["rudder"][:, 1] <= 1480)]
_sl = np.asarray(T["sil_l"], float)
OBS["strake_port_sil"] = _sl[(_sl[:, 1] >= 1085) & (_sl[:, 1] <= 1290)][:, :2]
# listens hjoerner (baandets sving fra akterspeilet til siden), lest av paa 3-5x-utsnitt
OBS["corners"] = np.array([[200.0, 641.0], [1095.0, 738.0]])
_sc = N.strake_corner()
CORN3 = np.array([[_sc[0] + 13.0, -(_sc[1] + 13.0), _sc[2]], [_sc[0] + 13.0, _sc[1] + 13.0, _sc[2]]])
SIG = dict(corners=4.0, strake_port_sil=3.0, strake_port=3.0, strake_port_in=3.0, strake_port_tr=3.0, strake_stbd_in=3.0, strake_stbd_tr=4.0, top=2.0,
           keel_l=2.5, keel_r=2.5, keel_bot=2.5, rudder=6.0)


def poly_dist(cam, X3, obs, cap=300.0):
    u, v, z = cam.project(X3)
    ok = z > 100
    Q = np.c_[u[ok], v[ok]]
    if len(Q) < 2:
        return np.full(len(obs), cap)
    a, b = Q[:-1], Q[1:]
    ab = b - a
    L2 = np.maximum((ab ** 2).sum(1), 1e-9)
    t = np.clip(((obs[:, None, :] - a[None]) * ab[None]).sum(2) / L2[None], 0.0, 1.0)
    pr = a[None] + t[..., None] * ab[None]
    d2 = ((obs[:, None, :] - pr) ** 2).sum(2)
    j = np.argmin(d2, axis=1)
    dv = obs - pr[np.arange(len(obs)), j]
    n = np.c_[-ab[j, 1], ab[j, 0]] / np.sqrt(L2[j])[:, None]
    d = (dv * n).sum(1)
    # punkter forbi endene av kurven: hele avstanden
    tj = t[np.arange(len(obs)), j]
    endd = np.sqrt(d2[np.arange(len(obs)), j])
    d = np.where((tj <= 0.0) | (tj >= 1.0), np.sign(d + 1e-9) * endd, d)
    return np.clip(d, -cap, cap)


def keel_parts(cam, dz=0.0):
    g = {}
    VK = VK0 + np.array([0.0, 0.0, dz])
    o = OBS["keel_l"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 1])
    g["keel_l"] = np.where(np.isfinite(lo), lo - o[:, 0], 150.0)
    o = OBS["keel_r"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 1])
    g["keel_r"] = np.where(np.isfinite(hi), hi - o[:, 0], 150.0)
    o = OBS["keel_bot"]; lo, hi = U.row_extents(cam, VK, FK, o[:, 0], axis="col")
    g["keel_bot"] = np.where(np.isfinite(hi), hi - o[:, 1], 150.0)
    return g


def parse(variant):
    parts = variant.split("_")
    return dict(mode=parts[0], lo="lo" in parts[1:], nok="nok" in parts[1:], rud="norud" not in parts[1:],
                kdz="kdz" in parts[1:], rtip="rtip" in parts[1:], corn="corn" in parts[1:])


def residuals(q, cfg, F, parts=False):
    cam = N.make_cam(q, cfg["mode"], W_, H_)
    nc = 7 + len(N.CAMX[cfg["mode"]])
    kdz = q[nc] if cfg["kdz"] else 0.0
    g = {}
    for k in ("strake_port", "strake_port_in", "strake_port_tr", "strake_stbd_in", "strake_stbd_tr", "top",
              "strake_port_sil"):
        g[k] = poly_dist(cam, F[k], OBS[k]) / SIG[k]
    if cfg.get("corn"):
        u, v, _ = cam.project(CORN3)
        g["corners"] = np.r_[u - OBS["corners"][:, 0], v - OBS["corners"][:, 1]] / SIG["corners"]
    if not cfg["nok"]:
        for k, v in keel_parts(cam, kdz).items():
            g[k] = v / SIG[k]
    if cfg["rud"]:
        g["rudder"] = poly_dist(cam, F["rudder"], OBS["rudder"]) / SIG["rudder"]
    if cfg.get("rtip"):
        # test: rorets nederste punkt (688, 1547) = forkant/bunn paa hengsellinja i z -1 047 (Enderlein)
        zb = -1047.0
        X = np.array([[C.transom_x(zb, 0.0) + P.RUDDER_GAP, 0.0, zb]])
        u, v, _ = cam.project(X)
        g["rtip"] = np.array([u[0] - 688.0, v[0] - 1547.0]) / 3.0
    pri = []
    ex = N.CAMX[cfg["mode"]]
    for k, val in zip(ex, q[7:nc]):
        if k in ("du", "dv"):
            pri.append(val / 300.0)
    if pri:
        g["prior"] = np.array(pri) * 4.0
    if parts:
        return g
    return np.concatenate([v / np.sqrt(max(len(v), 1) / 20.0) if k not in ("prior", "corners", "rtip") else v
                           for k, v in g.items()])


def solve(variant, starts=None):
    cfg = parse(variant)
    F = model_feats(-15.0 if cfg["lo"] else 0.0)
    ex = N.CAMX[cfg["mode"]]
    lb = [6000, -6000, -9000, 120, -89, -60, 300] + [N.LBX[k] for k in ex] + ([-400.0] if cfg["kdz"] else [])
    ub = [30000, 6000, 3000, 240, 30, 60, 12000] + [N.UBX[k] for k in ex] + ([400.0] if cfg["kdz"] else [])
    xs = [60, 30, 60, 0.3, 0.3, 0.3, 20] + [0.3 * N.XSX[k] for k in ex] + ([10.0] if cfg["kdz"] else [])
    if starts is None:
        # grovt kamera fra fire punkter (listens hjoerner, overkant midt, kjolens bunn): dbg-loesning
        starts = []
        for df in (0.8, 1.0, 1.3, 1.7):
            for dz in (0.0, -800.0):
                starts.append([9000.0 + 2500.0 * (df - 1.0), -350.0, -1114.0 + dz, 171.5, -31.0, 1.5, 1153.0 * df]
                              + [0.0] * len(ex))
    best = None
    for s in starts:
        s = list(s)[:7] + list(s[7:7 + len(ex)]) + [0.0] * max(0, 7 + len(ex) - len(s))
        s = [1.0 if (i >= 7 and ex[i - 7] == "asp" and abs(val) < 0.5) else val for i, val in enumerate(s)]
        if cfg["kdz"]:
            s = s + [0.0]
        s = np.clip(s, np.array(lb) + 1e-6, np.array(ub) - 1e-6)
        try:
            r = least_squares(lambda q: residuals(q, cfg, F), s, bounds=(lb, ub), x_scale=xs,
                              loss="soft_l1", f_scale=2.0, max_nfev=800)
        except Exception as e:      # noqa
            print("  start feilet:", e)
            continue
        if best is None or r.cost < best.cost:
            best = r
    g = residuals(best.x, cfg, F, True)
    rms = {k: round(float(np.sqrt(np.mean(np.square(v * SIG.get(k, 3.0 if k == "rtip" else 1.0))))), 2)
           for k, v in g.items()}
    return best, rms


if __name__ == "__main__":
    variants = sys.argv[1:] or ["pp", "pin", "k1", "ppk1", "pp_lo", "pp_nok", "pp_rud"]
    try:
        out = json.load(open(c.W + "/out/n1_cam.json"))
    except (OSError, ValueError):
        out = {"W": W_, "H": H_, "modes": {}}
    found = [np.array(m["q"][:7]) for m in out["modes"].values()]
    for v in variants:
        t0 = time.time()
        ex = N.CAMX[parse(v)["mode"]]
        starts = None
        if found:
            starts = [list(q) + [1.0 if k == "asp" else 0.0 for k in ex] for q in found]
            for df in (0.8, 1.0, 1.3, 1.7):
                starts.append([9000.0 + 2500.0 * (df - 1.0), -350.0, -1114.0, 171.5, -31.0, 1.5, 1153.0 * df]
                              + [0.0] * len(ex))
        best, rms = solve(v, starts)
        found.append(best.x[:7])
        q = best.x
        print(f"{v:9s} C=({q[0]:7.0f},{q[1]:6.0f},{q[2]:6.0f}) yaw {q[3]:6.2f} pitch {q[4]:6.2f} roll {q[5]:5.2f} "
              f"f {q[6]:6.0f} ekstra {np.round(q[7:], 3).tolist()} cost {best.cost:7.2f} | rms px {rms} "
              f"({time.time() - t0:.0f}s)", flush=True)
        out["modes"][v] = dict(q=best.x, mode=parse(v)["mode"], rms=rms, cost=best.cost)
        c.save_json(out, c.W + "/out/n1_cam.json")
