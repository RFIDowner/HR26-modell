"""Vurdering av dagens forkropp mot IMG_9387 (skriver bare til skjermen).

  1. resid per region med hovedkameraet (e9387.summary)
  2. samme med de andre kameraene i cam9387.json ('bt38', 'utenbt') -> hvor
     mye kameravalget flytter tallene
  3. foelsomhet: px per mm for dybde, bredde og stevnens x
  4. bildets bunnsilhuett tilbakeprojisert til modellens silhuettplan:
     omtrentlig z(x) for det laveste punktet, mot modellen
  5. kjolroten: bildets hulkil (rad 800-860) tilbakeprojisert til kjolsiden
     y = -120, mot modellens forkant
Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python vurder9387.py
"""
import json

import numpy as np

import common as c
import uwlib as U
import e9387 as E
import photos

P = c.P


def ray(cam, u, v):
    d = np.array([(u - cam.cx) / cam.f, (v - cam.cy) / cam.f, 1.0]) @ cam.R
    return cam.C, d


def hit_plane_y(cam, u, v, y0):
    o, d = ray(cam, u, v)
    t = (y0 - o[1]) / d[1]
    return o + t * d


def main():
    V, F = photos.mesh()
    print("== 1. dagens modell, hovedkamera 'fri'")
    E.summary(V, F, "13.11 kveld")

    print("\n== 2. kameravalg (middel px per region; + = modellen utenfor)")
    J = json.load(open(c.W + "/out/cam9387.json"))
    keep = E.CAM
    for m in ("fri", "bt38", "utenbt"):
        E.CAM = U.Cam(J["modes"][m]["p"], 2000, 1500)
        rf, rb = E.parts(V, F)
        s = []
        for name, kind, sel in E.REGIONS:
            mm = sel()
            s.append("%+6.1f" % (rf[mm] if kind == "f" else rb[mm]).mean())
        print("  %-7s" % m, " ".join(s), "  (", " | ".join(n.split(" (")[0] for n, _, _ in E.REGIONS), ")")
    E.CAM = keep

    print("\n== 3. foelsomhet (endring i middel-rest, px)")
    rf0, rb0 = E.parts(V, F)
    tests = [("bunnen 20 mm dypere (z<-100, x<3600)", lambda W: (W[:, 0] < 3600) & (W[:, 2] < -100), 2, -20.0),
             ("bunnen 50 mm bredere (z<-100, x<3600)", lambda W: (W[:, 0] < 3600) & (W[:, 2] < -100), 1, 50.0),
             ("vannlinjer 50 mm bredere (z -100..300)", lambda W: (W[:, 0] < 3800) & (W[:, 2] > -100) & (W[:, 2] < 300), 1, 50.0),
             ("forfoten 20 mm forover (x<1500, z<300)", lambda W: (W[:, 0] < 1500) & (W[:, 2] < 300), 0, -20.0)]
    for name, sel, ax, dv in tests:
        W = V.copy()
        m = sel(V)
        if ax == 1:
            W[m, 1] += dv * np.sign(V[m, 1])
        else:
            W[m, ax] += dv
        rf, rb = E.parts(W, F)
        print("  %-42s front %+5.1f  bunn %+5.1f" % (name, (rf - rf0).mean(), (rb - rb0).mean()))

    print("\n== 4. bunnens laveste punkt: bildet og modellen tilbakeprojisert til planet y = -100")
    print("     (samme plan for begge, saa planvalget faller ut; +-10 mm for y +-100)")
    T = E._T
    bot = np.asarray(T["bottom"], float)
    _, rb = E.parts(V, F)
    Xp = np.array([hit_plane_y(E.CAM, u, v, -100.0) for u, v in bot])
    Xm = np.array([hit_plane_y(E.CAM, u, v + r, -100.0) for (u, v), r in zip(bot, rb)])
    op, om = np.argsort(Xp[:, 0]), np.argsort(Xm[:, 0])
    print("      x     z_modell  z_bilde   bilde-modell")
    for x in range(1100, 3001, 100):
        if not (Xp[op, 0][0] <= x <= Xp[op, 0][-1]):
            continue
        zp = np.interp(x, Xp[op, 0], Xp[op, 2])
        zm = np.interp(x, Xm[om, 0], Xm[om, 2])
        # hull i sporet (stativ/roer): ingen verdi
        near = np.min(np.abs(Xp[:, 0] - x))
        flag = "" if near < 60 else "   (hull i sporet: interpolert)"
        print("  %6d %8.0f %8.0f   %+6.0f mm%s" % (x, zm, zp, zp - zm, flag))

    print("\n== 5. kjolroten: bildets kant og modellens (skrog + kjol) per rad, begge til planet y = -30")
    rr = np.asarray(T["root_rows"], float)
    a, b = E.keelroot(V, F)
    for i in range(0, len(rr), 3):
        Xp = hit_plane_y(E.CAM, rr[i, 1], rr[i, 0], -30.0)
        Xm = hit_plane_y(E.CAM, rr[i, 1] - a[i], rr[i, 0], -30.0)
        print("  rad %4.0f (z ~ %5.0f): bildet x %6.0f, modellen x %6.0f  ->  bildet %+5.0f mm forut (rest %+5.1f px)"
              % (rr[i, 0], Xp[2], Xp[0], Xm[0], Xm[0] - Xp[0], a[i]))
    rc = np.asarray(T["root_cols"], float)
    print("  per kolonne u %.0f-%.0f: modellen %+.1f px (middel) i forhold til bildet (- = modellen hoeyere)"
          % (rc[0, 0], rc[-1, 0], b.mean()))


if __name__ == "__main__":
    main()
