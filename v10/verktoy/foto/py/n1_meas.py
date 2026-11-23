"""Maal i «nye (1).jpeg» med kameraene i out/n1_cam.json (13.11.2026).

Spoersmaal 1: akterspeilets omriss.
  * knekkene i vannlinjestripens blaa overkant og i den lyse linja under
    den (overgangen til roedt) er akterspeilhjoernet i de hoeydene; de
    tilbakeprojiseres til akterspeilsflaten x = transom_x(z, y) -> (y, z)
  * hjoernelinja over stripen paa babord side (lys/skygge-grensa, 'knuckle')
    tilbakeprojiseres paa samme maate
  og sammenlignes med modellens hjoerne y(z) (n1_geo.corner_y).
Spoersmaal 2: skrogets omriss mot himmel (sil_l, sil_r) mot modellens
  omriss per rad, i px og mm (mm/px ved punktet som lager omrisset), med x
  for stasjonen som lager omrisset.

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python n1_meas.py [variant ...]
"""
import json
import sys

import numpy as np

import common as c
import uwlib as U
import n1_geo as N
import n1_cam as K

P, C = N.P, N.C
T = K.T
J = json.load(open(c.W + "/out/n1_cam.json"))["modes"]


def fit_kink(pts, uk, side_dir, a_side=60, a_tr=150, gap=6):
    """Knekken mellom akterspeilsdelen (rett) og sidedelen (krum) av en
    stripekant. side_dir = -1: sidedelen ligger til venstre for knekken."""
    p = np.asarray(pts, float)[:, :2]
    if side_dir < 0:
        sd = p[(p[:, 0] < uk - gap) & (p[:, 0] > uk - a_side)]
        tr = p[(p[:, 0] > uk + gap) & (p[:, 0] < uk + a_tr)]
    else:
        sd = p[(p[:, 0] > uk + gap) & (p[:, 0] < uk + a_side)]
        tr = p[(p[:, 0] < uk - gap) & (p[:, 0] > uk - a_tr)]
    ct = np.polyfit(tr[:, 0], tr[:, 1], 1)
    cs = np.polyfit(sd[:, 0], sd[:, 1], 2)
    r = np.roots(np.polysub(cs, ct))
    r = r[np.isreal(r)].real
    u = float(r[np.argmin(np.abs(r - uk))])
    rs = float(np.sqrt(np.mean((np.polyval(ct, tr[:, 0]) - tr[:, 1]) ** 2)))
    return u, float(np.polyval(ct, u)), rs


KINKS = {}
KINKS["bt_L"] = fit_kink(T["bt_top"], 465.0, -1)
KINKS["bt_R"] = fit_kink(T["bt_top"], 900.0, +1)
KINKS["cr_L"] = fit_kink(T["cream"], 555.0, -1, a_side=60, a_tr=100)
KINKS["cr_R"] = fit_kink(T["cream"], 812.0, +1, a_side=60, a_tr=100)

# hjoernelinja (babord) - glatt kurve, uteliggere ut
kn = np.asarray(T["knuckle"], float)[:, :2]
o = np.argsort(kn[:, 1])
kn = kn[o]
# glatt i parameter = buelengde; enkel filtrering mot et lokalt median
keep = np.ones(len(kn), bool)
for i in range(len(kn)):
    d = np.hypot(kn[:, 0] - kn[i, 0], kn[:, 1] - kn[i, 1])
    nb = kn[(d < 30) & (d > 0)]
    if len(nb) >= 3:
        cc = np.polyfit(nb[:, 1], nb[:, 0], 1) if np.ptp(nb[:, 1]) > np.ptp(nb[:, 0]) else None
        if cc is not None:
            keep[i] = abs(np.polyval(cc, kn[i, 1]) - kn[i, 0]) < 4.0
        else:
            cc = np.polyfit(nb[:, 0], nb[:, 1], 1)
            keep[i] = abs(np.polyval(cc, kn[i, 0]) - kn[i, 1]) < 4.0
KN = kn[keep]

ZG = np.arange(-420.0, 900.0, 5.0)
YM = np.array([(N.corner_y(float(z)) or (0, 0))[1] for z in ZG])


def model_y(z):
    return float(np.interp(z, ZG, YM))


def poly_cross(A, B):
    """Foerste skjaering mellom to polylinjer (n,2) i bildet, eller None."""
    for i in range(len(A) - 1):
        p, r = A[i], A[i + 1] - A[i]
        q = B[:-1]
        s_ = B[1:] - B[:-1]
        den = r[0] * s_[:, 1] - r[1] * s_[:, 0]
        ok = np.abs(den) > 1e-9
        t = np.where(ok, ((q[:, 0] - p[0]) * s_[:, 1] - (q[:, 1] - p[1]) * s_[:, 0]) / np.where(ok, den, 1), -1)
        w = np.where(ok, ((q[:, 0] - p[0]) * r[1] - (q[:, 1] - p[1]) * r[0]) / np.where(ok, den, 1), -1)
        hit = ok & (t >= 0) & (t <= 1) & (w >= 0) & (w <= 1)
        if hit.any():
            j = int(np.argmax(hit))
            return p + t[j] * r
    return None


RTIP = (688.0, 1547.0)      # rorets nederste punkt i bildet (forkant/bunn), +-3 px


def hinge_z(cam, u, v):
    """Naermeste punkt paa hengsellinja (forkanten, y = 0) til strålen
    gjennom (u, v): (x, z, avstand mm)."""
    o = cam.C
    d = cam.ray(np.array([u]), np.array([v]))[0]
    a = np.array([P.RUDDER_X, 0.0, P.RUDDER_TOP_Z])
    b = np.array([P.RUDDER_X + P.RUDDER_RAKE, 0.0, P.RUDDER_BOT_Z])
    e = (b - a) / np.linalg.norm(b - a)
    w0 = o - a
    A_, B_, C_ = d @ d, d @ e, e @ e
    D_, E_ = d @ w0, e @ w0
    den = A_ * C_ - B_ * B_
    s_ = (B_ * E_ - C_ * D_) / den
    t = (A_ * E_ - B_ * D_) / den
    X = a + t * e
    return float(X[0]), float(X[2]), float(np.linalg.norm(o + s_ * d - X))


def run(var):
    m = J[var]
    cam = N.make_cam(np.array(m["q"]), m["mode"], K.W_, K.H_)
    res = {"kinks": {}, "knuckle": [], "img": {}}
    # i bildet: modellens hjoerne mot stripekantene (uavhengig av stripens hoeyde)
    bt = np.asarray(T["bt_top"], float)[:, :2]
    cr = np.asarray(T["cream"], float)[:, :2]
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        cl = N.corner_line(-420.0, None, 5.0, sgn)
        u, v, _ = cam.project(cl)
        A = np.c_[u, v][::-1]          # ovenfra og ned
        for key, line in (("bt", bt), ("cr", cr)):
            X = poly_cross(A, line[np.argsort(line[:, 0])])
            k = KINKS[key + "_" + side]
            if X is None:
                continue
            Pp = N.on_transom(cam, k[0], k[1]); Pm = N.on_transom(cam, X[0], X[1])
            res["img"][key + "_" + side] = dict(u_photo=k[0], u_model=float(X[0]), v_model=float(X[1]),
                                                du=float(k[0] - X[0]), y_photo=abs(float(Pp[1])),
                                                y_model=abs(float(Pm[1])), z_photo=float(Pp[2]), z_model=float(Pm[2]))
    # roret: nederste punkt
    hx, hz, hd = hinge_z(cam, *RTIP)
    hz2 = [hinge_z(cam, RTIP[0] + du, RTIP[1] + dv)[1] for du, dv in ((0, 3), (0, -3), (3, 0), (-3, 0))]
    res["rudder_tip"] = dict(x=hx, z=hz, miss_mm=hd, z_range=[min(hz2), max(hz2)])
    for k, (u, v, rs) in KINKS.items():
        X = N.on_transom(cam, u, v)
        X2 = N.on_transom(cam, u + 1.0, v)
        res["kinks"][k] = dict(u=u, v=v, y=abs(float(X[1])), z=float(X[2]), y_model=model_y(float(X[2])),
                               mmpx=float(np.linalg.norm(X2 - X)), side=float(np.sign(X[1])))
    for u, v in KN:
        X = N.on_transom(cam, u, v)
        if X is None:
            continue
        res["knuckle"].append([float(u), float(v), abs(float(X[1])), float(X[2]), model_y(float(X[2]))])
    # spoersmaal 2: omriss
    V, F = N.hull_mesh()
    sil = {}
    for key, use_lo in (("sil_l", True), ("sil_r", False)):
        a = np.asarray(T[key], float)
        rows = a[:, 1]
        lo, hi = U.row_extents(cam, V, F, rows)
        mod = lo if use_lo else hi
        d = a[:, 0] - mod                      # + = bildet lenger til hoeyre
        out_px = -d if use_lo else d           # + = bildet stikker lenger UT enn modellen
        # mm per px ved omrisset: dybden til naermeste nett-punkt som projiseres der
        u, vv, zc = cam.project(V)
        rows_info = []
        for (uu, r, dark), mm_, op in zip(a, mod, out_px):
            if not np.isfinite(mm_):
                rows_info.append(None)
                continue
            j = np.argmin((u - mm_) ** 2 + (vv - r) ** 2)
            rows_info.append(dict(v=float(r), u_photo=float(uu), u_model=float(mm_), out_px=float(op),
                                  mm_px=float(zc[j] / cam.f), out_mm=float(op * zc[j] / cam.f),
                                  x=float(V[j, 0]), y=float(V[j, 1]), z=float(V[j, 2]), strap=bool(dark)))
        sil[key] = rows_info
    res["sil"] = sil
    return res


def summary(var, r):
    print(f"=== {var}  (rms {J[var]['rms']})")
    for k, d in r["img"].items():
        print(f"  i bildet {k}: knekk u {d['u_photo']:6.1f}, modellens hjoerne krysser samme stripekant ved u "
              f"{d['u_model']:6.1f} (du {d['du']:+5.1f} px) -> y foto {d['y_photo']:4.0f} / modell {d['y_model']:4.0f}"
              f" = {d['y_photo'] - d['y_model']:+5.0f} mm (z {d['z_photo']:4.0f} / {d['z_model']:4.0f})")
    rt = r["rudder_tip"]
    print(f"  rorets bunn (forkant): z {rt['z']:6.0f} (+-3 px: {rt['z_range'][0]:.0f}..{rt['z_range'][1]:.0f}), "
          f"x {rt['x']:5.0f}, bom {rt['miss_mm']:.0f} mm")
    for k, d in r["kinks"].items():
        print(f"  knekk {k}: u {d['u']:6.1f} v {d['v']:6.1f} -> z {d['z']:5.0f}  y foto {d['y']:4.0f}  "
              f"y modell {d['y_model']:4.0f}  diff {d['y'] - d['y_model']:+5.0f} mm  ({d['mmpx']:.2f} mm/px)")
    kn = np.array(r["knuckle"])
    if len(kn):
        for z0, z1 in ((150, 250), (250, 350), (350, 450), (450, 550), (550, 650), (650, 750)):
            s = kn[(kn[:, 3] >= z0) & (kn[:, 3] < z1)]
            if len(s):
                print(f"  hjoerne z {z0}-{z1}: n {len(s):2d}  y foto {np.mean(s[:, 2]):4.0f}  y modell "
                      f"{np.mean(s[:, 4]):4.0f}  diff {np.mean(s[:, 2] - s[:, 4]):+5.0f} mm")
    for key in ("sil_l", "sil_r"):
        rows = [q for q in r["sil"][key] if q is not None and not q["strap"]]
        for v0, v1 in ((1100, 1250), (1250, 1400), (1400, 1550), (1550, 1700), (1700, 1860)):
            s = [q for q in rows if v0 <= q["v"] < v1]
            if s:
                print(f"  {key} v {v0}-{v1}: n {len(s):2d}  ut {np.mean([q['out_px'] for q in s]):+6.1f} px = "
                      f"{np.mean([q['out_mm'] for q in s]):+5.0f} mm  (x {np.mean([q['x'] for q in s]):5.0f}, "
                      f"z {np.mean([q['z'] for q in s]):5.0f})")


if __name__ == "__main__":
    vs = sys.argv[1:] or list(J.keys())
    print("knekker i bildet:", {k: (round(v[0], 1), round(v[1], 1), round(v[2], 2)) for k, v in KINKS.items()})
    print("hjoernelinje: %d av %d punkter beholdt" % (len(KN), len(kn)))
    allr = {}
    for v in vs:
        r = run(v)
        allr[v] = r
        summary(v, r)
    c.save_json(dict(kinks_px=KINKS, knuckle_px=KN, res=allr), c.W + "/out/n1_meas.json")
