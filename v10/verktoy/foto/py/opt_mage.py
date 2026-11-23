"""Trinn 9 «magen» (14.11.2026): fyll midjen under vann mellom vinduets forkant
og ca. 7 m, saa vannlinjene blir jevne (uten midje), uten aa roere noe utenfor.

Spantfamilien er som foer (en superellipse fra kjolpunktet til dekkskanten med
bunnreisning, utfall og eksponent). Tabellene faar et TILLEGG som er null for
t <= T0 og t >= T1 og har null stigning der (pchip med nullpunkter utenfor), saa
alt foran vinduet og alt aktenfor ca. 7 m er bit for bit som foer.

Tilleggene finnes ved minste kvadrater:
  * jevnhet: annenderiverte langs baaten av halvbredden i faste hoeyder
    (vannlinjer over og under DWL), fra litt foran T0 til litt bak T1
  * tak: halvbredden i hver hoeyde skal ikke bli stoerre enn den stoerste som
    finnes i dag ved eller foran vinduets forkant + 400 mm («ikke tykkere paa
    midten»)
  * oversiden (z >= 200) holdes naer dagens
  * tilleggene selv skal vaere glatte

  python ../../../../tools/memcap.py --gb 3 -- python opt_mage.py [--skriv]

Skriver tabellen (og med --skriv: out/opt_mage.json).
"""
import json
import math
import sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, __file__.replace("\\", "/").rsplit("/", 5)[0])     # repo-roten
from hr26 import curves as C          # noqa: E402
from hr26 import params as P          # noqa: E402

T0, T1 = 0.45, 0.88
KNOTS = [0.49, 0.53, 0.57, 0.61, 0.65, 0.69, 0.73, 0.77, 0.81, 0.85]
ZS = [600.0, 300.0, 100.0, 0.0, -100.0, -200.0, -300.0, -380.0]
XS = np.arange(3000.0, 7400.1, 50.0)
BASE = dict(dead=C._pchip(P.SECTION_DEADRISE), n=C._pchip(P.SECTION_N), flare=C._pchip(P.SECTION_FLARE))


def bump(vals):
    return C._pchip([(0.0, 0.0), (T0, 0.0)] + list(zip(KNOTS, vals)) + [(T1, 0.0), (1.0, 0.0)])


def install(p):
    k = len(KNOTS)
    db, dn, df = bump(p[:k]), bump(p[k:2 * k]), bump(p[2 * k:3 * k])
    C._DEADRISE = lambda t: BASE["dead"](t) + db(t)
    C._NEXP = lambda t: max(BASE["n"](t) + dn(t), 1.6)
    C._FLARE = lambda t: BASE["flare"](t) + df(t)
    C._GEOM.clear()


def waterlines():
    Y = np.full((len(ZS), len(XS)), np.nan)
    for j, x in enumerate(XS):
        p = C._section_geom(float(x))["pts"]
        zz = np.maximum.accumulate(p[:, 1])
        for i, z in enumerate(ZS):
            if z > p[0, 1] + 1.0:
                Y[i, j] = np.interp(z, zz, p[:, 0])
    return Y


def area_curve():
    out = []
    for x in XS:
        p = C._section_geom(float(x))["pts"]
        zz = np.maximum.accumulate(p[:, 1])
        m = p[:, 1] <= 0.0
        yw = float(np.interp(0.0, zz, p[:, 0]))
        out.append(2 * abs(np.trapezoid(np.r_[p[m, 0], yw], np.r_[p[m, 1], 0.0])) / 1e6)
    return np.array(out)


install(np.zeros(3 * len(KNOTS)))
Y0 = waterlines()
A0 = area_curve()
V0 = C.displaced_volume_m3()
x_cap = XS <= P.WIN_X0 + 400.0
CAP = np.nanmax(Y0[:, x_cap], axis=1)
W_FAIR = np.array([0.5, 0.5, 0.7, 1.0, 1.0, 1.0, 1.0, 1.0])
ZONE = (XS >= T0 * P.LOA - 400.0) & (XS <= T1 * P.LOA + 300.0)


def resid(p):
    install(p)
    Y = waterlines()
    r = []
    for i, z in enumerate(ZS):
        y = Y[i]
        d2 = (y[2:] - 2 * y[1:-1] + y[:-2])[ZONE[1:-1]]          # mm per (50 mm)^2
        r.append(W_FAIR[i] * 4.0 * np.nan_to_num(d2))
        if z <= 0.0:
            over = np.nan_to_num(y - CAP[i] - 5.0)
            r.append(0.5 * np.clip(over, 0.0, None))
        if z >= 200.0:
            r.append(0.05 * np.nan_to_num(y - Y0[i]))
    k = len(KNOTS)
    for a, w in ((p[:k], 1.0), (p[k:2 * k], 8.0), (p[2 * k:], 2.0)):
        e = np.r_[0.0, a, 0.0]
        r.append(w * 0.6 * (e[2:] - 2 * e[1:-1] + e[:-2]))
    return np.concatenate(r)


def main():
    k = len(KNOTS)
    p0 = np.zeros(3 * k)
    lo = np.r_[np.full(k, -30.0), np.full(k, -3.0), np.full(k, -6.0)]
    hi = np.r_[np.full(k, 10.0), np.full(k, 4.0), np.full(k, 12.0)]
    r0 = resid(p0)
    sol = least_squares(resid, p0, bounds=(lo, hi), x_scale=np.r_[np.full(k, 5.0), np.full(k, 0.5), np.full(k, 2.0)],
                        diff_step=1e-2, max_nfev=120, verbose=0)
    p = sol.x
    install(p)
    Y = waterlines()
    A = area_curve()
    V = C.displaced_volume_m3()
    print("kost foer %.0f  etter %.0f   (%d evalueringer)" % (float(r0 @ r0), float(sol.fun @ sol.fun), sol.nfev))
    print("knute t      x     d bunnreisn.  d eksponent  d utfall   ->  bunnreisn.   n     utfall")
    for i, t in enumerate(KNOTS):
        print("  %.2f  %6.0f   %+8.1f     %+7.2f    %+6.1f       %6.1f    %5.2f   %5.1f" % (
            t, t * P.LOA, p[i], p[k + i], p[2 * k + i], C._DEADRISE(t), C._NEXP(t), C._FLARE(t)))
    print("halvbredde (mm), foer -> etter:")
    print("     x   " + "".join("   z %5.0f     " % z for z in ZS) + "  areal m2")
    for j in range(0, len(XS), 10):
        print("  %5.0f  " % XS[j] + "".join(" %5.0f->%5.0f  " % (Y0[i, j], Y[i, j]) for i in range(len(ZS)))
              + " %.3f->%.3f" % (A0[j], A[j]))
    print("kanobunn %.3f -> %.3f m3;  stoerste areal %.3f -> %.3f m2 ved x %.0f -> %.0f" % (
        V0, V, A0.max(), A.max(), XS[A0.argmax()], XS[A.argmax()]))
    out_zone = (XS < T0 * P.LOA - 1.0) | (XS > T1 * P.LOA + 1.0)
    print("stoerste endring utenfor sonen: %.4f mm" % float(np.nanmax(np.abs(Y - Y0)[:, out_zone])))
    if "--skriv" in sys.argv:
        tab = dict(T0=T0, T1=T1, knots=KNOTS, deadrise=[round(float(v), 2) for v in p[:k]],
                   n=[round(float(v), 3) for v in p[k:2 * k]], flare=[round(float(v), 2) for v in p[2 * k:]],
                   vol=[V0, V])
        json.dump(tab, open(__file__.replace("\\", "/").rsplit("/", 2)[0] + "/out/opt_mage.json", "w"), indent=1)
        print("skrev out/opt_mage.json")
    return p, Y, A


if __name__ == "__main__":
    main()
