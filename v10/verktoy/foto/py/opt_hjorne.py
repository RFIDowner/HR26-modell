"""Akterspeilets hjoerne (trinn 4, kvelden 13.11.2026): formen akter tilpasses
eierens blaa prikker paa hjoernet i IMG_9391 (out/blaa9391.json), i tillegg til
omrisset akterfra (IMG_9391), forfra (IMG_9388), volumet og at siden over
fenderlisten staar stille. Uten CAD.

Prikkene tilbakeprojiseres til akterspeilsflaten (hjorne9391.py), saa hvert
punkt er (y, z) paa akterspeilet. Modellens hjoerne i hoeyden z er spantets
halvbredde der spantet skjaerer akterspeilet: x = transom_x(z, y), y = spant(x, z).
Avviket er avstanden i (y, z)-planet paa akterspeilet, i mm.

Kjoeres fra denne mappa: python opt_hjorne.py [sjekk]
"""
import json
import sys
import time

import numpy as np
from scipy.optimize import least_squares

import common as c, uwlib as U, hjerte as Hj, photos as PH
import opt_hjerte as OH

import os
KAM = os.environ.get("KAM9391", "")
if KAM:
    PH.CAM91 = U.Cam(json.load(open(c.W + "/out/cam9391e.json"))[KAM]["p"][:7], 1500, 2000)
HJ = json.load(open(c.W + "/out/hjorne9391%s.json" % ("_" + KAM if KAM else "")))
DOTS = np.array([(r["y_photo"], r["z"], r["mmpx"]) for k in ("left", "right") for r in HJ["res"][k]])
SIDE = np.array([0] * len(HJ["res"]["left"]) + [1] * len(HJ["res"]["right"]))
# de nederste prikkene ligger ved rorets kant (venstre) eller paa roret (hoeyre): lav vekt
WDOT = np.where(DOTS[:, 1] < -150.0, 0.3, 1.0)
ZG = np.arange(-260.0, 420.0, 10.0)


def corner_yz(C, zg=ZG):
    """Modellens hjoerne (y, z) paa akterspeilet for hoeydene zg."""
    out = []
    for z in zg:
        y = 400.0
        for _ in range(4):
            x = float(U.transom_x(z, y))
            p = C._section_geom(round(x, 1))["pts"]
            zz = np.maximum.accumulate(p[:, 1])
            if z <= zz[0]:
                y = 0.0
                break
            y = float(np.interp(z, zz, p[:, 0]))
        out.append((y, z))
    return np.array(out)


def dot_dist(Cyz):
    """Fortegnsavstand (mm) fra hver prikk til modellens hjoernelinje; + = modellen bredere."""
    A, B = Cyz[:-1], Cyz[1:]
    d = []
    for (y, z, _) in DOTS:
        Pp = np.array([y, z])
        AB = B - A
        t = np.clip(np.einsum("ij,ij->i", Pp - A, AB) / np.maximum(np.einsum("ij,ij->i", AB, AB), 1e-9), 0, 1)
        Q = A + t[:, None] * AB
        dd = np.hypot(*(Q - Pp).T)
        i = int(np.argmin(dd))
        ym = float(np.interp(z, Cyz[:, 1], Cyz[:, 0]))
        d.append(dd[i] * (1.0 if ym >= y else -1.0))
    return np.array(d)


# --- frie parametre ----------------------------------------------------------
NAMES = ["d75", "d90", "d95", "d100", "n80", "n90", "n95", "n100", "h68", "h74", "h78", "w68", "w74", "w78"]


def base():
    """Dagens tabeller (HEAD) som utgangspunkt."""
    P = c.P
    return dict(SECTION_N=list(P.SECTION_N), SECTION_DEADRISE=list(P.SECTION_DEADRISE),
                DEADWOOD_H=list(P.DEADWOOD_H), DEADWOOD_W=list(P.DEADWOOD_W))


Hj.apply({})
B0 = base()
dr = dict(B0["SECTION_DEADRISE"]); nn = dict(B0["SECTION_N"]); dh = dict(B0["DEADWOOD_H"]); dw = dict(B0["DEADWOOD_W"])
Q_HEAD = [dr[0.75], dr[0.90], 0.5 * (dr[0.90] + dr[1.00]), dr[1.00], nn[0.80],
          float(np.interp(0.90, [0.8, 1.0], [nn[0.80], nn[1.00]])), float(np.interp(0.95, [0.8, 1.0], [nn[0.80], nn[1.00]])),
          nn[1.00], dh[6800.0], dh[7400.0], dh[7800.0], dw[6800.0], dw[6800.0], dw[6800.0]]
LB = [0, 0, 0, 0, 1.6, 1.6, 1.6, 1.6, 0, 0, 0, 40, 40, 40]
UB = [45, 45, 45, 45, 8.0, 8.0, 8.0, 8.0, 300, 380, 420, 400, 400, 400]


NO95 = "uten95" in sys.argv


def params(q):
    d75, d90, d95, d100, n80, n90, n95, n100, h68, h74, h78, w68, w74, w78 = q
    if NO95:
        d95, n95 = 0.5 * (d90 + d100), 0.5 * (n90 + n100)
    o = base()
    o["SECTION_DEADRISE"] = [k for k in B0["SECTION_DEADRISE"] if k[0] < 0.75] + \
        [(0.75, d75), (0.90, d90), (0.95, d95), (1.00, d100)]
    o["SECTION_N"] = [k for k in B0["SECTION_N"] if k[0] < 0.80] + \
        [(0.80, n80), (0.90, n90), (0.95, n95), (1.00, n100)]
    o["DEADWOOD_H"] = [k for k in B0["DEADWOOD_H"] if k[0] < 6800.0] + \
        [(6800.0, h68), (7400.0, h74), (7800.0, h78), (8000.0, h78)]
    o["DEADWOOD_W"] = [k for k in B0["DEADWOOD_W"] if k[0] < 6800.0] + \
        [(6800.0, w68), (7400.0, w74), (7800.0, w78)]
    return o


VOLT, VOLS = 2.30, 0.25
TS = np.arange(0.66, 1.0001, 0.01)
XS = TS * c.P.LOA
KS = float(dict(a.split("=") for a in sys.argv[1:] if "=" in a).get("glatt", 1.0))
# start=<tag> skal ikke inn i filnavnet


def smooth_terms(C):
    """Krumningen (andre differanse paa 0,01 i t) av bunnreisning, slag, doedtre
    og overgangsbredde langs de siste 34 % av skroget."""
    dd = np.array([C._DEADRISE(t) for t in TS])
    nn_ = np.array([C._NEXP(t) for t in TS])
    hh = np.array([C._DEADWOOD(x) for x in XS])
    ww = np.array([C._DWW(x) for x in XS])
    return KS * np.r_[np.diff(dd, 2) * 3.0, np.diff(nn_, 2) * 30.0, np.diff(hh, 2) * 0.3, np.diff(ww, 2) * 0.3]
W91, W88S, W88B, WCOR = 1.0, 0.3, 0.3, 1.0


def resid(q, parts=False):
    C = Hj.apply(params(q))
    PH.c.C = C
    V, F = PH.mesh()
    a, b = PH.e9391(V, F)
    l8, r8, b8 = PH.e9388(V, F)
    vol = U.hydro()["vol"]
    tc = OH.top_change(C)
    cyz = corner_yz(C)
    dc = dot_dist(cyz)
    dcp = dc / DOTS[:, 2] * WDOT                      # i piksler, vektet
    g = dict(e91=np.r_[a, b] * W91 / np.sqrt(len(a) + len(b)) * 5,
             e88s=np.r_[l8, r8] * W88S / np.sqrt(len(l8) + len(r8)) * 5,
             e88b=b8 * W88B / np.sqrt(len(b8)) * 5,
             cor=dcp * WCOR / np.sqrt(len(dcp)) * 5,
             vol=np.array([(vol - VOLT) / VOLS * 10.0]),
             top=np.array([max(0.0, tc - 10.0) * 5.0]),
             smooth=smooth_terms(C))
    if parts:
        return g, dict(vol=vol, top=tc, e91=(a, b), e88=(l8, r8, b8), cor=dc, cyz=cyz, gap=Hj.keel_gap(C))
    return np.concatenate(list(g.values()))


def report(tag, q):
    g, info = resid(q, True)
    a, b = info["e91"]; l8, r8, b8 = info["e88"]; dc = info["cor"]
    f = lambda e: f"{np.mean(e):+6.1f}/{np.sqrt(np.mean(e ** 2)):5.1f}"
    up = DOTS[:, 1] >= -150.0
    print(f"{tag:10s} 9391 L {f(a)} R {f(b)} | 9388 L {f(l8)} R {f(r8)} bot {f(b8)} | hjoerne mm "
          f"V {f(dc[(SIDE == 0) & up])} H {f(dc[(SIDE == 1) & up])} | vol {info['vol']:.3f} top {info['top']:.1f} "
          f"| kjol->skrog {info['gap']:.0f}", flush=True)
    return info


if __name__ == "__main__":
    t0 = time.time()
    report("HEAD", Q_HEAD)
    print("tid per evaluering %.1f s" % (time.time() - t0))
    TAG = "_".join(a.replace("=", "") for a in sys.argv[1:] if not a.startswith("start=")) or "std"
    if KAM:
        TAG += "_" + KAM
    if "sjekk" in sys.argv:
        sys.exit(0)
    ARG = dict(a.split("=") for a in sys.argv[1:] if "=" in a)
    for i, k in ((4, "n80max"), (5, "n90max"), (6, "n95max"), (7, "n100max")):
        if k in ARG:
            UB[i] = float(ARG[k])
    Q0 = Q_HEAD
    if "start" in ARG:
        Q0 = list(np.clip(json.load(open(c.W + "/out/opt_hjorne_%s.json" % ARG["start"]))["q"], LB, UB))
        report("start", Q0)
    r = least_squares(resid, Q0, bounds=(LB, UB),
                      x_scale=[2, 2, 2, 2, 0.2, 0.2, 0.2, 0.2, 15, 15, 15, 15, 15, 15],
                      diff_step=1e-3, max_nfev=150, loss="soft_l1", f_scale=3.0)
    print("tid %.0f s, cost %.1f" % (time.time() - t0, r.cost))
    print(dict(zip(NAMES, np.round(r.x, 1).tolist())))
    info = report("tilpasset", r.x)
    c.save_json(dict(q=r.x, names=NAMES, params=params(r.x), vol=info["vol"], top=info["top"], gap=info["gap"],
                     cor=info["cor"], cyz=info["cyz"]), c.W + "/out/opt_hjorne_%s.json" % TAG)
