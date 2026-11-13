"""Skeptikerens kamera for «nye (3).jpeg» (13.11.2026). Andre ankre enn
n3_cam.py: fenderlisten (eget spor), vannlinjestripens overkant langs
styrbord side (z fra IMG_9370, bt_top_z) og, i noen varianter, kjolen.
IKKE listens hjoerner og IKKE rorhodet (de testes i stedet).
Varianter: hullkamera, fritt hovedpunkt, fritt pikselforhold, med og uten kjol.

Maal: listens hjoerner (forutsagt mot observert), styrbord hjoernelinje
(eget spor) tilbakeprojisert til akterspeilsflaten, stripens overkant paa
akterspeilet, og rorets nederste punkt.

BILDET VISER FOLK: bare tall i repoet.
Kjoeres:  python ../../../../tools/memcap.py --gb 3 -- python chk_n3_cam.py
"""
import json
import os

import numpy as np
from scipy.optimize import least_squares

import common as c
import uwlib as U
import n1_geo as N          # bare modellgeometri (hjoerne, liste, akterspeil), ingen resultater
import geo9374 as G

P, C = N.P, N.C
HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, "..", "out", "chk_n3_trace.json")))
W_, H_ = T["W"], T["H"]
CX, CY = 585.0, 1265.5          # midt i selve bildet (svarte felt over og under)
VK, FK = N.keel_mesh()

strake_obs = np.array(T["strake"])[:, :2]
bt = np.array(T["bt"])[:, :2]
bt_side = bt[(bt[:, 0] > 640) & (bt[:, 0] < 975)]          # til hoeyre for knekken (u ca. 595)
bt_tr = bt[(bt[:, 0] > 455) & (bt[:, 0] < 575)]           # akterspeilet, mellom roret og knekken
kl = np.array(T["keel_l"], float); kr = np.array(T["keel_r"], float); kb = np.array(T["keel_bot"], float)
kl = kl[(kl[:, 1] >= 1600) & (kl[:, 1] <= 1730)]; kr = kr[(kr[:, 1] >= 1600) & (kr[:, 1] <= 1730)]
KN = np.array(T["knuckle"])[:, :2]
KN = KN[KN[:, 1] > 1100]

S3 = np.vstack([N.strake_transom(-1.0), N.strake_transom(1.0)[::-1][1:], N.strake_side(1.0, 3000.0, 150)[::-1]])
xe = N.strake_corner()[0]
xs = np.linspace(5000.0, 7795.0, 120)
BT3 = np.array([[x, G.side_y(x, float(G.bt_top_z(x))), float(G.bt_top_z(x))] for x in xs])
BT3 = BT3[np.isfinite(BT3[:, 1])]
BT3 = np.array([p for p in BT3 if p[0] < C.transom_x(p[2], p[1])])
SC = N.strake_corner()
CORN3 = np.array([[SC[0] + 13.0, -(SC[1] + 13.0), SC[2]], [SC[0] + 13.0, SC[1] + 13.0, SC[2]]])
CORN_OBS = np.array([[22.0, 1062.0], [785.0, 1046.0]])   # babord: ytterste listepunkt; styrbord: knekken i listen


class Cam(N.Cam):
    pass


def make(q, mode):
    du = dv = 0.0; asp = 1.0; k1 = 0.0
    ex = q[7:]
    if "pp" in mode:
        du, dv = ex[0], ex[1]; ex = ex[2:]
    if "asp" in mode:
        asp = ex[0]; ex = ex[1:]
    return N.Cam(q[:7], W_, H_, du=du, dv=(CY - H_ / 2.0) + dv, asp=asp, k1=k1)


def poly_dist(cam, X3, obs):
    u, v, z = cam.project(X3)
    Pp = np.c_[u, v]
    a, b = Pp[:-1], Pp[1:]
    ab = b - a
    L2 = np.maximum((ab ** 2).sum(1), 1e-9)
    d = np.empty(len(obs))
    for i, o in enumerate(obs):
        t = np.clip(((o - a) * ab).sum(1) / L2, 0, 1)
        pr = a + t[:, None] * ab
        d[i] = np.sqrt(((pr - o) ** 2).sum(1)).min()
    return d


def residuals(q, mode, keel, parts=False):
    cam = make(q, mode)
    g = {"strake": poly_dist(cam, S3, strake_obs) / 2.0,
         "bt_side": poly_dist(cam, BT3, bt_side) / 3.0}
    if keel:
        lo, hi = U.row_extents(cam, VK, FK, kl[:, 1])
        g["keel_l"] = np.where(np.isfinite(lo), lo - kl[:, 0], 150.0) / 2.5
        lo, hi = U.row_extents(cam, VK, FK, kr[:, 1])
        g["keel_r"] = np.where(np.isfinite(hi), hi - kr[:, 0], 150.0) / 2.5
        lo, hi = U.row_extents(cam, VK, FK, kb[:, 0], axis="col")
        g["keel_bot"] = np.where(np.isfinite(hi), hi - kb[:, 1], 150.0) / 2.5
    if "pp" in mode:
        g["prior_pp"] = np.array(q[7:9]) / 200.0
    if "asp" in mode:
        g["prior_asp"] = np.array([(q[-1] - 1.0) / 0.10])
    if parts:
        return g
    return np.concatenate([v / np.sqrt(max(len(v), 1) / 20.0) if not k.startswith("prior") else v
                           for k, v in g.items()])


def solve(mode, keel):
    ex = (["pp"] if "pp" in mode else []) and [0.0, 0.0]
    ex = ([0.0, 0.0] if "pp" in mode else []) + ([1.0] if "asp" in mode else [])
    lb = [8000, -3500, -1500, 160, -30, -20, 400] + ([-400, -400] if "pp" in mode else []) + ([0.7] if "asp" in mode else [])
    ub = [26000, 3500, 2500, 200, 40, 20, 9000] + ([400, 400] if "pp" in mode else []) + ([1.3] if "asp" in mode else [])
    xsc = [60, 30, 30, 0.3, 0.3, 0.3, 20] + ([5, 5] if "pp" in mode else []) + ([0.01] if "asp" in mode else [])
    best = None
    for X, Y, Z, f in ((11500, 1200, 200, 1700), (12500, 800, 0, 2000), (14000, 1500, 400, 2400),
                       (10500, 1000, 300, 1400)):
        s = [X, Y, Z, 189.0, 3.0, -1.0, f] + ex
        r = least_squares(lambda q: residuals(q, mode, keel), s, bounds=(lb, ub), x_scale=xsc, loss="soft_l1",
                          f_scale=2.0, max_nfev=500)
        if best is None or r.cost < best.cost:
            best = r
    g = residuals(best.x, mode, keel, True)
    sig = dict(strake=2.0, bt_side=3.0, keel_l=2.5, keel_r=2.5, keel_bot=2.5)
    rms = {k: round(float(np.sqrt(np.mean(np.square(v * sig.get(k, 1.0))))), 2) for k, v in g.items()}
    return best, rms


def ray_at_x(cam, u, v, x):
    d = cam.ray(np.array([u]), np.array([v]))[0]
    t = (x - cam.C[0]) / d[0]
    X = cam.C + t * d
    return float(X[1]), float(X[2])


ZG = np.arange(-420.0, 900.0, 5.0)
YM = np.array([(N.corner_y(float(z)) or (0, 0))[1] for z in ZG])


if __name__ == "__main__":
    out = {"modes": {}}
    tip = T["rudder_tip"]
    rst = np.array(T["rudder_stripe"], float)
    for keel in (False, True):
        for mode in ("pin", "pp", "asp", "ppasp"):
            name = mode + ("_kjol" if keel else "")
            best, rms = solve(mode, keel)
            q = best.x
            cam = make(q, mode)
            u, v, _ = cam.project(CORN3)
            cres = np.c_[u, v] - CORN_OBS
            # hjoernelinja -> akterspeilsflaten
            kn = []
            for uu, vv in KN:
                X = N.on_transom(cam, uu, vv)
                if X is not None:
                    kn.append([uu, vv, abs(float(X[1])), float(X[2]), float(np.interp(X[2], ZG, YM))])
            kn = np.array(kn)
            bins = {}
            for z0, z1 in ((125, 175), (175, 250), (250, 350), (350, 450), (450, 550), (550, 650), (650, 760)):
                s_ = kn[(kn[:, 3] >= z0) & (kn[:, 3] < z1)]
                if len(s_):
                    bins["%d-%d" % (z0, z1)] = [len(s_), round(float(np.mean(s_[:, 2])), 0),
                                                round(float(np.mean(s_[:, 4])), 0),
                                                round(float(np.mean(s_[:, 2] - s_[:, 4])), 0)]
            # knekkpunktet der hjoernelinja moeter stripen (nederste sporpunkt)
            low = kn[np.argmax(kn[:, 1])]
            # stripens overkant paa akterspeilet
            bz = [N.on_transom(cam, a, b) for a, b in bt_tr]
            bz = [float(X[2]) for X in bz if X is not None]
            # roret
            zt = {int(x): ray_at_x(cam, tip[0], tip[1], x)[1] for x in (7673.0, 7900.0, 8086.0, 8150.0)}
            # stripen paa roret (x ca. 7 830 midt i roret oeverst)
            zrs_top = float(np.mean([ray_at_x(cam, a, b, 7830.0)[1] for a, b, _ in rst]))
            zrs_red = float(np.mean([ray_at_x(cam, a, cc, 7830.0)[1] for a, _, cc in rst]))
            # mm per px ved akterspeilet (vannrett), i hjoernet
            u1, v1, _ = cam.project(np.array([[SC[0], SC[1], SC[2]], [SC[0], SC[1] - 100.0, SC[2]]]))
            mmpx = 100.0 / abs(u1[0] - u1[1])
            print(f"{name:11s} C=({q[0]:6.0f},{q[1]:5.0f},{q[2]:5.0f}) yaw {q[3]:6.2f} pit {q[4]:5.2f} rol {q[5]:5.2f} "
                  f"f {q[6]:5.0f} ex {np.round(q[7:], 3).tolist()} rms {rms}")
            print(f"   hjoerner (forutsagt - observert) px: babord {cres[0].round(1).tolist()} styrbord "
                  f"{cres[1].round(1).tolist()}  ({mmpx:.2f} mm/px)")
            print(f"   hjoernelinja foto-modell: {bins}")
            print(f"   nederste punkt (moeter stripen): u {low[0]:.0f} v {low[1]:.0f} -> y {low[2]:.0f} z {low[3]:.0f}"
                  f" (modell {low[4]:.0f})")
            print(f"   stripens overkant paa akterspeilet: z {np.mean(bz):.0f} (n {len(bz)}); paa roret: blaa "
                  f"{zrs_top:.0f}, roedt {zrs_red:.0f}")
            print(f"   rorets spiss z ved x 7673/7900/8086/8150: {', '.join('%.0f' % zt[k] for k in zt)}")
            out["modes"][name] = dict(q=q.tolist(), rms=rms, corner_res=cres.tolist(), bins=bins,
                                      low=low.tolist(), stripe_tr_z=float(np.mean(bz)), rudder_tip_z=zt,
                                      rudder_stripe_z=[zrs_top, zrs_red], mm_per_px=mmpx, knuckle=kn.tolist())
    c.save_json(out, os.path.join(HERE, "..", "out", "chk_n3_cam.json"))
