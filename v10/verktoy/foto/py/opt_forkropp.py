"""Forkroppen (trinn 5, kvelden 13.11.2026): bunnreisning, slag og doedtre
fra baugen til t 0,60 tilpasses bildene av forkroppen og glatte vannlinjer.
Akterskipet fra trinn 4 (t >= 0,75 og doedtreet fra x 6 800) staar fast.

Eieren: modellen ser ut som en hvithai med en klump paa magen. Aarsaken: flat
bunn (bunnreisning 0-4 grader) fra x 1,6 til 3,6 m som gaar over i V-bunn mot
x 4,8 m, saa vannlinjene under DWL buler ut ved x 3,7 m, og et doedtre som
starter 0,5 m foran kjolen.

Maal (vektet minste kvadrat):
  * glatte vannlinjer: endringen i krumning langs x (z -300 ... +300)
  * bildene: IMG_9388 (forfra), IMG_9391 (akterfra) og de nye e<NNNN>.py
    (forkroppen, laget av maaleagentene) naar de finnes
  * kanobunnens volum (svakt), siden over fenderlisten staar stille
Kjoeres fra denne mappa: python opt_forkropp.py [sjekk] [glatt=K] [utenfoto] [foto=9395,9387,...]
"""
import importlib
import json
import sys
import time

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares

import common as c, uwlib as U, hjerte as Hj, photos as PH
import opt_hjerte as OH

ARG = dict(a.split("=") for a in sys.argv[1:] if "=" in a)
KS = float(ARG.get("glatt", 1.0))
MED88 = "med9388" in sys.argv
FOTO = [f for f in ARG.get("foto", "").split(",") if f]
EMOD = {}
for f in FOTO:
    try:
        EMOD[f] = importlib.import_module("e" + f)
    except Exception as exc:              # pragma: no cover
        print("advarsel: e%s kunne ikke lastes (%s)" % (f, exc))

Hj.apply({})
P0 = {k: list(getattr(c.P, k)) for k in ("SECTION_N", "SECTION_DEADRISE", "DEADWOOD_H", "DEADWOOD_W")}

NAMES = ["d127", "d20", "d30", "d45", "d60", "n0", "n15", "n30", "n45", "n60", "hmid", "xdw", "w59"]
dr = dict(P0["SECTION_DEADRISE"]); nn = dict(P0["SECTION_N"])
def _at(tab, x):
    t = np.array(tab, float)
    return float(np.interp(x, t[:, 0], t[:, 1]))


Q_HEAD = [_at(P0["SECTION_DEADRISE"], 0.127), _at(P0["SECTION_DEADRISE"], 0.20), _at(P0["SECTION_DEADRISE"], 0.30),
          _at(P0["SECTION_DEADRISE"], 0.45), _at(P0["SECTION_DEADRISE"], 0.60), _at(P0["SECTION_N"], 0.0),
          _at(P0["SECTION_N"], 0.15), _at(P0["SECTION_N"], 0.30), _at(P0["SECTION_N"], 0.45), _at(P0["SECTION_N"], 0.60),
          _at(P0["DEADWOOD_H"], 5900.0), float(P0["DEADWOOD_H"][0][0]) if P0["DEADWOOD_H"][0][1] == 0.0 else 2900.0,
          _at(P0["DEADWOOD_W"], 5900.0)]
LB = [5, 0, 0, 0, 0, 1.6, 2.0, 2.0, 2.0, 2.0, 0, 3380, 80]
UB = [45, 45, 45, 45, 40, 3.5, 6.0, 6.0, 6.0, 6.0, 150, 5200, 300]


def params(q):
    d127, d20, d30, d45, d60, n0, n15, n30, n45, n60, hmid, xdw, w59 = q
    o = {}
    o["SECTION_DEADRISE"] = [(0.00, dr[0.0]), (0.127, d127), (0.20, d20), (0.30, d30), (0.45, d45), (0.60, d60)] + \
        [k for k in P0["SECTION_DEADRISE"] if k[0] >= 0.75]
    o["SECTION_N"] = [(0.00, n0), (0.15, n15), (0.30, n30), (0.45, n45), (0.60, n60)] + \
        [k for k in P0["SECTION_N"] if k[0] >= 0.80]
    o["DEADWOOD_H"] = [(xdw, 0.0), (xdw + 500.0, hmid), (5900.0, hmid)] + \
        [k for k in P0["DEADWOOD_H"] if k[0] >= 6800.0]
    o["DEADWOOD_W"] = [(5900.0, w59)] + [k for k in P0["DEADWOOD_W"] if k[0] >= 6800.0]
    return o


XG = np.arange(300.0, 7700.0, 50.0)
ZW = (-300.0, -200.0, -100.0, 0.0, 150.0, 300.0)


def waterlines(C):
    """Halvbredden y(x) i hoeydene ZW (NaN under bunnen og aktenfor akterspeilet)."""
    Y = np.full((len(ZW), len(XG)), np.nan)
    for j, x in enumerate(XG):
        p = C._section_geom(float(x))["pts"]
        zz = np.maximum.accumulate(p[:, 1])
        for i, z in enumerate(ZW):
            if z > zz[0] and x < U.transom_x(z, 0.0) - 60.0:
                Y[i, j] = np.interp(z, zz, p[:, 0])
    return Y


def fair_terms(Y):
    """Endringen i krumning (1/m per 50 mm) langs hver vannlinje, uten de
    300 mm naermest endene der vannlinjen starter mot senterlinjen. Fast
    lengde (len(XG) - 3 per vannlinje), 0 der vannlinjen ikke finnes."""
    out = []
    for y in Y:
        ys = np.full(len(y), np.nan)
        ok = np.isfinite(y) & (y > 60.0)
        idx = np.nonzero(ok)[0]
        if len(idx) >= 20:
            br = np.nonzero(np.diff(idx) > 1)[0]
            r = max(np.split(idx, br + 1), key=len)[6:-6]
            if len(r) >= 12:
                ys[r] = gaussian_filter1d(y[r], 2.0)
        k = np.diff(ys, 2) / 50.0 ** 2 * 1000.0          # 1/m
        j = np.diff(k) * 40.0
        out.append(np.where(np.isfinite(j), j, 0.0))
    return np.concatenate(out)


VOLT, VOLS = 2.20, 0.30


def resid(q, parts=False):
    C = Hj.apply(params(q))
    PH.c.C = C
    V, F = PH.mesh()
    a, b = PH.e9391(V, F)
    l8, r8, b8 = PH.e9388(V, F)
    vol = U.hydro()["vol"]
    tc = OH.top_change(C)
    Y = waterlines(C)
    fr = fair_terms(Y)
    g = dict(fair=fr * KS / np.sqrt(0.6 * len(fr)) * 5,
             e91=np.r_[a, b] / np.sqrt(len(a) + len(b)) * 5,
             vol=np.array([(vol - VOLT) / VOLS * 5.0]),
             top=np.array([max(0.0, tc - 10.0) * 5.0]))
    if MED88:   # IMG_9388-kameraet (cam9388_rail1: f 2068 mot ca. 1500, laast paa stripen) er ikke paalitelig
        g["e88s"] = np.r_[l8, r8] * 0.5 / np.sqrt(len(l8) + len(r8)) * 5
        g["e88b"] = b8 * 0.5 / np.sqrt(len(b8)) * 5
    for f, m in EMOD.items():
        e = np.asarray(m.resid(V, F), float)
        w = getattr(m, "WEIGHTS", None)
        if w is not None and len(w) == len(e):
            e = e * w
        e = np.where(np.isfinite(e), e, 0.0)
        g["e" + f] = e / np.sqrt(max(len(e), 1)) * 5
        if hasattr(m, "resid_bow"):
            eb = np.asarray(m.resid_bow(V, F), float)
            eb = np.where(np.isfinite(eb), eb, 0.0)
            g["bow" + f] = eb * 0.7 / np.sqrt(max(len(eb), 1)) * 5
    if parts:
        return g, dict(vol=vol, top=tc, Y=Y, gap=Hj.keel_gap(C))
    return np.concatenate(list(g.values()))


def report(tag, q):
    g, info = resid(q, True)
    rms = {k: float(np.sqrt(np.mean(np.square(v)))) for k, v in g.items()}
    Y = info["Y"]
    bulge = []
    for i, z in enumerate(ZW[:3]):
        y = Y[i]
        j = np.nanargmax(y)
        bulge.append("z%d: maks %.0f ved x %.0f" % (z, y[j], XG[j]))
    print(f"{tag:10s} " + " ".join(f"{k} {v:.2f}" for k, v in rms.items()) +
          f" | vol {info['vol']:.3f} top {info['top']:.1f} kjol->skrog {info['gap']:.0f} | " + "; ".join(bulge), flush=True)
    return g, info


if __name__ == "__main__":
    t0 = time.time()
    report("HEAD", Q_HEAD)
    print("tid per evaluering %.1f s" % (time.time() - t0))
    if "sjekk" in sys.argv:
        sys.exit(0)
    Q0 = list(np.clip(Q_HEAD, LB, UB))
    if "start" in ARG:
        Q0 = list(np.clip(json.load(open(c.W + "/out/opt_forkropp_%s.json" % ARG["start"]))["q"], LB, UB))
    r = least_squares(resid, Q0, bounds=(LB, UB),
                      x_scale=[2, 2, 2, 2, 2, 0.1, 0.2, 0.2, 0.2, 0.2, 10, 50, 15],
                      diff_step=1e-3, max_nfev=150, loss="soft_l1", f_scale=3.0)
    print("tid %.0f s, cost %.1f" % (time.time() - t0, r.cost))
    print(dict(zip(NAMES, np.round(r.x, 1).tolist())))
    g, info = report("tilpasset", r.x)
    tag = "_".join(a.replace("=", "").replace(",", "-") for a in sys.argv[1:] if not a.startswith("start=")) or "std"
    c.save_json(dict(q=r.x, names=NAMES, params=params(r.x), vol=info["vol"], top=info["top"], gap=info["gap"]),
                c.W + "/out/opt_forkropp_%s.json" % tag)
