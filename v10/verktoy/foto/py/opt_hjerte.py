"""Samlet tilpasning av formen under vann (trinn 3, 13.11.2026 kveld).

Frie parametre: bunnreisningen (SECTION_DEADRISE, t 0,30-1,00), slaget
(SECTION_N, t 0,45/0,80/1,00), doedtreet (DEADWOOD_H midtskips 3 600-5 900 og
ved 6 800/7 400/7 800) og bredden paa den hule overgangen (DEADWOOD_W ved
5 900/6 800). Maal: omrisset i IMG_9391 (vekt 1), IMG_9388 (sider og bunn,
vekt 0,3), kanobunnens volum 2,3 +- 0,25 m3 (448-5: DEPL 2,36 m3 med kjol og
ror), skrogsiden over fenderlisten flytter seg hoyst 10 mm, glatte tabeller.

Kjoeres fra denne mappa: python opt_hjerte.py
"""
import json, time
import numpy as np
from scipy.optimize import least_squares
import common as c, uwlib as U, hjerte as Hj, photos as PH

XS_TOP = np.arange(300, 7801, 250.0)
Hj.apply(Hj.U_PATCH)
TOP0 = []
for x in XS_TOP:
    p = np.array(c.C.section(float(x), 400)); zs = c.C.strake_z(float(x))
    TOP0.append(p[p[:, 1] >= zs - 30])
Hj.apply({})
TOPH = []
for x in XS_TOP:
    p = np.array(c.C.section(float(x), 400)); zs = c.C.strake_z(float(x))
    TOPH.append(p[p[:, 1] >= zs - 30])


def top_change(C):
    worst = 0.0
    for x, p0 in zip(XS_TOP, TOPH):
        p = np.array(C.section(float(x), 400))
        o = np.argsort(p[:, 1])
        y = np.interp(p0[:, 1], p[o, 1], p[o, 0])
        worst = max(worst, float(np.max(np.abs(y - p0[:, 0]))))
    return worst


NAMES = ["d30", "d45", "d60", "d75", "d90", "d100", "n45", "n80", "n100",
         "hmid", "h68", "h74", "h78", "w59", "w68"]
Q0 = [4.0, 6.0, 16.0, 26.0, 15.0, 3.0, 4.0, 4.0, 3.8, 0.0, 100.0, 170.0, 210.0, 180.0, 180.0]
LB = [0, 0, 0, 0, 0, 0, 2.6, 2.6, 2.6, 0, 0, 0, 0, 80, 80]
UB = [30, 35, 40, 45, 45, 40, 6.0, 6.0, 6.0, 150, 250, 300, 330, 400, 400]


def params(q):
    d30, d45, d60, d75, d90, d100, n45, n80, n100, hmid, h68, h74, h78, w59, w68 = q
    over = dict(Hj.U_PATCH)
    over["SECTION_DEADRISE"] = [(0.00, 45.0), (0.127, 15.0), (0.20, 4.0), (0.30, d30), (0.45, d45),
                                (0.60, d60), (0.75, d75), (0.90, d90), (1.00, d100)]
    over["SECTION_N"] = [(0.00, 2.4), (0.15, 3.1), (0.30, 3.4), (0.45, n45), (0.80, n80), (1.00, n100)]
    over["DEADWOOD_H"] = [(2900.0, 0.0), (3600.0, hmid), (5900.0, hmid), (6800.0, h68), (7400.0, h74),
                          (7800.0, h78), (8000.0, h78)]
    over["DEADWOOD_W"] = [(5900.0, w59), (6800.0, w68)]
    return over


VOLT, VOLS = 2.30, 0.25
W91, W88S, W88B = 1.0, 0.3, 0.3


def resid(q, parts=False):
    C = Hj.apply(params(q))
    PH.c.C = C
    V, F = PH.mesh()
    a, b = PH.e9391(V, F)
    l8, r8, b8 = PH.e9388(V, F)
    vol = U.hydro()["vol"]
    tc = top_change(C)
    d = np.array(q[:6])
    hh = np.array([q[9], q[10], q[11], q[12]])
    g = dict(e91=np.r_[a, b] * W91 / np.sqrt(len(a) + len(b)) * 5,
             e88s=np.r_[l8, r8] * W88S / np.sqrt(len(l8) + len(r8)) * 5,
             e88b=b8 * W88B / np.sqrt(len(b8)) * 5,
             vol=np.array([(vol - VOLT) / VOLS * 10.0]),
             top=np.array([max(0.0, tc - 10.0) * 5.0]),
             smooth=np.r_[np.diff(d, 2) * 1.0, np.diff(hh, 2) * 0.05])
    if parts:
        return g, dict(vol=vol, top=tc, e91=(a, b), e88=(l8, r8, b8), gap=Hj.keel_gap(C))
    return np.concatenate(list(g.values()))


def report(tag, q):
    g, info = resid(q, True)
    a, b = info["e91"]; l8, r8, b8 = info["e88"]
    f = lambda e: f"{np.mean(e):+6.1f}/{np.sqrt(np.mean(e ** 2)):5.1f}"
    print(f"{tag:10s} 9391 L {f(a)} R {f(b)} | 9388 L {f(l8)} R {f(r8)} bot {f(b8)} | vol {info['vol']:.3f} "
          f"top {info['top']:.1f} | kjol->skrog {info['gap']:.0f}", flush=True)
    return info


if __name__ == "__main__":
    report("start", Q0)
    t0 = time.time()
    r = least_squares(resid, Q0, bounds=(LB, UB),
                      x_scale=[2, 2, 2, 2, 2, 2, 0.2, 0.2, 0.2, 15, 15, 15, 15, 20, 20],
                      diff_step=1e-3, max_nfev=120, loss="soft_l1", f_scale=3.0)
    print("tid %.0f s, cost %.1f" % (time.time() - t0, r.cost))
    print(dict(zip(NAMES, np.round(r.x, 1).tolist())))
    info = report("tilpasset", r.x)
    c.save_json(dict(q=r.x, names=NAMES, vol=info["vol"], top=info["top"], gap=info["gap"]),
                c.W + "/out/opt_hjerte.json")
