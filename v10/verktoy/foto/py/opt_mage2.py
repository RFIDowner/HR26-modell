"""Trinn 9 «magen» (14.11.2026), runde 2: fyll buken under vann mellom
vinduets forkant og ca. 6,5-7 m, glatt, og mot bildene.

Tillegg til SECTION_DEADRISE, SECTION_N og SECTION_FLARE som er null for
t <= T0 og t >= T1 med null stigning der (opt_mage.install), saa alt foran
vinduet (x < 3 578) og aktenfor ca. 7 000 er bit for bit som foer.

Maal (minste kvadrater, hvert ledd skalert til ca. 1 per «merkbar» feil):
  fair    annenderiverte langs baaten av vannlinjer (z 300 ... -380) og
          diagonaler (fra senterlinjen i DWL, 30/45/60 grader ned) i sonen
  n1      «nye 1» (aktenfra, nedenfra): bildets omriss rad 1300-1700 mot
          modellens, tre kameravarianter. Bare der bildet ligger UTENFOR
          modellen teller det fullt; innenfor teller det svakt. 10 px = 1.
  e91     IMG_9391 (akterfra, 1,8 m bak): omrisset skal ikke bli verre enn
          i dag (sterkt): 2 px = 1. Laaser spantene ved x 6 200-7 000.
  cap     halvbredden i hver hoeyde under DWL skal ikke bli stoerre enn den
          stoerste foran vinduet + 400 mm, og stoerste spantareal ikke
          stoerre enn i dag («ikke tykkere paa midten»)
  top     siden over vann (z 300, 600) staar nesten stille
  reg     tilleggene selv er glatte

  python ../../../../tools/memcap.py --gb 3 -- python opt_mage2.py [n1=VEKT] [top=VEKT] [tag=NAVN]

Skriver tabellen og ../out/opt_mage2_<tag>.json (samme form som opt_mage.json).
"""
import json
import math
import sys
import time

import numpy as np
from scipy.optimize import least_squares

import common as c
import uwlib as U
import photos as PH
import n1_geo as N
import n1_cam as K
import opt_mage as M

ARG = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
W_N1 = float(ARG.get("n1", 1.0))
W_TOP = float(ARG.get("top", 1.0))
W_FAIR = float(ARG.get("fair", 1.0))
W_KONV = float(ARG.get("konv", 0.0))     # straff for hul (konkav) vannlinje/diagonal i sonen: midjen
W_MIN = float(ARG.get("min", 0.0))       # straff for endring under vann (minst mulig fyll)
TAG = ARG.get("tag", "std")
ROW0, ROW1 = float(ARG.get("rad0", 1300)), float(ARG.get("rad1", 1700))

KN = M.KNOTS
k = len(KN)
J = json.load(open(c.W + "/out/n1_cam.json"))["modes"]
VARS = ("ppk1_corn", "ppk12", "pp_corn")
CAMS = [N.make_cam(np.array(J[v]["q"]), J[v]["mode"], K.W_, K.H_) for v in VARS]
SIL = {}
for key in ("sil_l", "sil_r"):
    a = np.asarray(K.T[key], float)
    m = (a[:, 2] == 0) & (a[:, 1] >= ROW0) & (a[:, 1] <= ROW1)
    SIL[key] = a[m]

DIAG = [(0.0, 30.0), (0.0, 45.0), (0.0, 60.0), (250.0, 45.0)]   # (z0 paa senterlinjen, vinkel ned fra vannrett)
XF = np.arange(3200.0, 7400.1, 50.0)
ZONE_F = (XF >= M.T0 * c.P.LOA - 300.0) & (XF <= M.T1 * c.P.LOA + 300.0)
ZW = [300.0, 100.0, 0.0, -100.0, -200.0, -300.0, -380.0]


def lines():
    """Vannlinjer (ZW) og diagonaler (DIAG) som (n, len(XF)), mm."""
    out = np.full((len(ZW) + len(DIAG), len(XF)), np.nan)
    for j, x in enumerate(XF):
        p = c.C._section_geom(float(x))["pts"]
        zz = np.maximum.accumulate(p[:, 1])
        for i, z in enumerate(ZW):
            if z > p[0, 1] + 1.0:
                out[i, j] = np.interp(z, zz, p[:, 0])
        for i, (z0, ang) in enumerate(DIAG):
            a = math.radians(ang)
            along = p[:, 0] * math.cos(a) - (p[:, 1] - z0) * math.sin(a)
            perp = p[:, 0] * math.sin(a) + (p[:, 1] - z0) * math.cos(a)
            s = np.nonzero((perp[:-1] < 0.0) & (perp[1:] >= 0.0))[0]
            if len(s):
                q = s[0]
                t = -perp[q] / (perp[q + 1] - perp[q])
                out[len(ZW) + i, j] = along[q] + t * (along[q + 1] - along[q])
    return out


def n1_out(V, F):
    """+ = bildets omriss utenfor modellens, px, alle kameraer og begge sider."""
    r = []
    for cam in CAMS:
        for key, use_lo in (("sil_l", True), ("sil_r", False)):
            a = SIL[key]
            lo, hi = U.row_extents(cam, V, F, a[:, 1])
            mod = lo if use_lo else hi
            d = a[:, 0] - mod
            r.append(np.nan_to_num(-d if use_lo else d))
    return np.concatenate(r)


M.install(np.zeros(3 * k))
L0 = lines()
V0, F0 = U.hull_mesh(140, 48)
A91L0, A91R0 = PH.e9391(V0, F0)
E91_0 = np.r_[A91L0, A91R0]
N1_0 = n1_out(V0, F0)
AMAX0 = float(M.A0.max())
BASE_DEAD = np.array([M.BASE["dead"](t) for t in KN])
BASE_N = np.array([M.BASE["n"](t) for t in KN])


def resid(p, parts=False):
    M.install(p)
    L = lines()
    V, F = U.hull_mesh(140, 48)
    g = {}
    # glatthet: annenderiverte (mm per 50 mm^2) i sonen
    fr = []
    for i in range(len(L)):
        y = L[i]
        d2 = (y[2:] - 2 * y[1:-1] + y[:-2])[ZONE_F[1:-1]]
        fr.append(np.nan_to_num(d2))
    g["fair"] = W_FAIR * 2.0 * np.concatenate(fr)
    if W_KONV > 0.0:
        # midjen: positiv annenderivert (hul i plan) over 200 mm-steg, linjer under z 150
        kv = []
        for i in range(len(L)):
            if i < len(ZW) and (ZW[i] > 150.0 or ZW[i] < -350.0):
                continue      # z -380 ligger nede i doedtreets hule overgang
            y = L[i]
            d2 = (y[8:] - 2 * y[4:-4] + y[:-8])[ZONE_F[4:-4]]
            kv.append(np.clip(np.nan_to_num(d2), 0.0, None))
        g["konv"] = W_KONV * 0.5 * np.concatenate(kv)
    if W_MIN > 0.0:
        g["min"] = W_MIN * np.nan_to_num(L[2:] - L0[2:]).ravel() / 20.0
    # nye 1
    o = n1_out(V, F)
    g["n1"] = W_N1 * np.where(o > 0.0, o, 0.3 * o) / 10.0 / math.sqrt(len(CAMS))
    # IMG_9391: ikke verre enn i dag (avvik fra bildet, men baseline-rms trekkes fra)
    a, b = PH.e9391(V, F)
    e = np.r_[a, b]
    g["e91"] = (e - E91_0) / 2.0 * 0.5 + np.clip(np.abs(e) - np.abs(E91_0), 0.0, None) / 2.0
    # tak: halvbredde under DWL og spantareal
    Y = M.waterlines()
    cap = []
    for i, z in enumerate(M.ZS):
        if z <= 0.0:
            cap.append(np.clip(np.nan_to_num(Y[i] - M.CAP[i] - 3.0), 0.0, None) / 1.0)
    A = M.area_curve()
    cap.append(np.clip(A - AMAX0 - 0.002, 0.0, None) / 0.002)
    g["cap"] = np.concatenate(cap)
    # siden over vann
    g["top"] = W_TOP * np.r_[np.nan_to_num(L[0] - L0[0]) / 10.0, np.nan_to_num(Y[0] - M.Y0[0]) / 5.0]
    # tilleggene glatte
    reg = []
    for a_, w in ((p[:k], 0.3), (p[k:2 * k], 3.0), (p[2 * k:], 0.6)):
        e_ = np.r_[0.0, a_, 0.0]
        reg.append(w * (e_[2:] - 2 * e_[1:-1] + e_[:-2]))
    g["reg"] = np.concatenate(reg)
    if parts:
        return g, dict(L=L, Y=Y, A=A, e91=e, n1=o)
    return np.concatenate(list(g.values()))


def report(tag, p):
    g, info = resid(p, True)
    cost = {kk: float(v @ v) for kk, v in g.items()}
    o = info["n1"]
    e = info["e91"]
    print("%-10s kost " % tag + " ".join("%s %.0f" % (kk, v) for kk, v in cost.items())
          + " | n1 ut %.1f px (foer %.1f) | 9391 rms %.1f (foer %.1f) middel L/R %+.1f/%+.1f | vol %.3f" % (
              o.mean(), N1_0.mean(), np.sqrt(np.mean(e ** 2)), np.sqrt(np.mean(E91_0 ** 2)),
              e[:len(A91L0)].mean(), e[len(A91L0):].mean(), c.C.displaced_volume_m3()), flush=True)
    return g, info


def main():
    t0 = time.time()
    p0 = np.zeros(3 * k)
    if "start" in ARG:
        d = json.load(open(c.W + "/out/" + ARG["start"]))
        p0 = np.r_[d["deadrise"], d["n"], d["flare"]]
    report("foer", np.zeros(3 * k))
    lo = np.r_[-BASE_DEAD + 0.0, np.full(k, -1.0), np.full(k, -6.0)]
    nmax = float(ARG.get("nmax", 6.5))   # trinn 4: slaget akter holdes mykt (n <= 5 ved t 0,80)
    hi = np.r_[np.full(k, 12.0), np.maximum(nmax - BASE_N, 1e-3), np.full(k, 10.0)]
    p0 = np.clip(p0, lo + 1e-6, hi - 1e-6)
    sol = least_squares(resid, p0, bounds=(lo, hi), x_scale=np.r_[np.full(k, 3.0), np.full(k, 0.3), np.full(k, 1.5)],
                        diff_step=1e-3, max_nfev=int(ARG.get("nfev", 200)), loss="linear",
                        ftol=float(ARG.get("ftol", 1e-8)), xtol=1e-10)
    p = sol.x
    print("tid %.0f s, %d evalueringer" % (time.time() - t0, sol.nfev))
    g, info = report("forslag", p)
    print("knute t      x     d bunnreisn.  d eksponent  d utfall   ->  bunnreisn.   n     utfall")
    for i, t in enumerate(KN):
        print("  %.2f  %6.0f   %+8.1f     %+7.2f    %+6.1f       %6.1f    %5.2f   %5.1f" % (
            t, t * c.P.LOA, p[i], p[k + i], p[2 * k + i], c.C._DEADRISE(t), c.C._NEXP(t), c.C._FLARE(t)))
    L, Y, A = info["L"], info["Y"], info["A"]
    names = ["z %4.0f" % z for z in ZW] + ["diag %3.0f/%2.0f" % d for d in DIAG]
    print("linjer, foer -> forslag (mm):")
    for i, nm in enumerate(names):
        print("  %-12s" % nm + " ".join("%5.0f>%-5.0f" % (L0[i, j], L[i, j]) for j in range(0, len(XF), 8)))
    print("  x           " + " ".join("%11.0f" % XF[j] for j in range(0, len(XF), 8)))
    print("areal       " + " ".join("%5.3f>%-5.3f" % (M.A0[j], A[j]) for j in range(0, len(M.XS), 8)))
    print("x           " + " ".join("%11.0f" % M.XS[j] for j in range(0, len(M.XS), 8)))
    out_zone = (M.XS < M.T0 * c.P.LOA - 1.0) | (M.XS > M.T1 * c.P.LOA + 1.0)
    print("stoerste endring utenfor sonen: %.4f mm" % float(np.nanmax(np.abs(Y - M.Y0)[:, out_zone])))
    tab = dict(T0=M.T0, T1=M.T1, knots=KN, deadrise=[round(float(v), 3) for v in p[:k]],
               n=[round(float(v), 4) for v in p[k:2 * k]], flare=[round(float(v), 3) for v in p[2 * k:]],
               vol=[M.V0, c.C.displaced_volume_m3()], args=ARG)
    path = c.W + "/out/opt_mage2_%s.json" % TAG
    json.dump(tab, open(path, "w"), indent=1)
    print("skrev", path)


if __name__ == "__main__":
    main()
