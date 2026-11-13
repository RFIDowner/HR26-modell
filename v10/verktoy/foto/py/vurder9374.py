"""Vurdering av forkroppen mot IMG_9374 (skriver bare til skjermen).

  1. resid per region med hovedkameraet og de andre kameraene (e9374.summary)
     for modellen eieren saa (commit geo9374.MODEL_REV, foer trinn 5)
  2. det samme for arbeidstreet slik det ligger naa (trinn 5 underveis i
     hovedoekta) - bare til orientering
  3. foelsomhet: hvor mye flytter dybde, bredde, bunnreisning og forfot
     omrisset (px)
  4. bildets bunnsilhuett tilbakeprojisert til modellens silhuettpunkt:
     omtrentlig z(x) for det laveste punktet, mot modellen
  5. kjolroten og doedtreet (klumpen): hva bildet viser og ikke viser
Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python vurder9374.py
"""
import numpy as np

import common as c
import uwlib as U
import geo9374 as G
import e9374 as E

P = c.P


def undistort(cam, u, v):
    """Bildepunkt -> normaliserte koordinater (a, b) for Cam9374 (k1, asp)."""
    ad = (u - cam.cx) / cam.f
    bd = (v - cam.cy) / (cam.f * cam.asp)
    a, b = ad, bd
    for _ in range(30):
        s = 1.0 + cam.k1 * (a * a + b * b)
        a, b = ad / s, bd / s
    return a, b


def ray(cam, u, v):
    a, b = undistort(cam, u, v)
    d = np.array([a, b, 1.0]) @ cam.R
    return cam.C, d / np.linalg.norm(d)


def hit_plane_y(cam, u, v, y0):
    o, d = ray(cam, u, v)
    t = (y0 - o[1]) / d[1]
    return o + t * d


def perturbed(V, sel, fn):
    W = V.copy()
    m = sel(V)
    W[m] = fn(V[m])
    return W


def main():
    G.use_model()
    V, F = U.hull_mesh(220, 60)
    print("== 1. modellen eieren saa (commit %s), hovedkamera '%s'" % (G.MODEL_REV, E._CJ["main"]))
    E.summary(V, F, "commit " + G.MODEL_REV, alt=True)
    rf0, rb0 = E.parts(V, F)

    print("\n== 2. arbeidstreet naa (trinn 5 underveis i hovedoekta, til orientering)")
    G.use_model(None)
    VW, FW = U.hull_mesh(220, 60)
    E._KM = None
    E.summary(VW, FW, "arbeidstreet")
    G.use_model()
    E._KM = None

    print("\n== 3. foelsomhet (endring i middel-rest, px; + = modellen lenger ut)")
    bx = lambda W: (W[:, 0] > 1000) & (W[:, 0] < 3600)
    tests = [
        ("bunnen 20 mm dypere (z<-100, x 1000-3600)", lambda W: bx(W) & (W[:, 2] < -100),
         lambda X: X + [0, 0, -20.0]),
        ("bunnen 50 mm bredere (z<-100, x 1000-3600)", lambda W: bx(W) & (W[:, 2] < -100),
         lambda X: X + np.c_[0 * X[:, 0], 50.0 * np.sign(X[:, 1]), 0 * X[:, 0]]),
        ("vannlinjer 50 mm bredere (z -100..300)", lambda W: (W[:, 0] < 3800) & (W[:, 2] > -100) & (W[:, 2] < 300),
         lambda X: X + np.c_[0 * X[:, 0], 50.0 * np.sign(X[:, 1]), 0 * X[:, 0]]),
        ("V-bunn: senterlinjen 30 mm ned, 0 ved |y|=400", lambda W: bx(W) & (W[:, 2] < -100),
         lambda X: X + np.c_[0 * X[:, 0], 0 * X[:, 0], -30.0 * np.clip(1 - np.abs(X[:, 1]) / 400.0, 0, 1)]),
        ("slaget 30 mm ned (|y| 300-900, z<-100)", lambda W: bx(W) & (W[:, 2] < -100) & (np.abs(W[:, 1]) > 300),
         lambda X: X + np.c_[0 * X[:, 0], 0 * X[:, 0], -30.0 * np.clip((np.abs(X[:, 1]) - 300) / 300.0, 0, 1)]),
        ("forfoten 20 mm forover (x<1500, z<300)", lambda W: (W[:, 0] < 1500) & (W[:, 2] < 300),
         lambda X: X + [-20.0, 0, 0]),
    ]
    reg = [(n, k, s()) for n, k, s in E.REGIONS]
    print("  %-46s %s" % ("", "  ".join("%9s" % n.split(":")[0].split(" (")[0][-9:] for n, _, _ in reg)))
    for name, sel, fn in tests:
        W = perturbed(V, sel, fn)
        rf, rb = E.parts(W, F)
        vals = [((rf - rf0) if k == "f" else (rb - rb0))[m].mean() for _, k, m in reg]
        print("  %-46s %s" % (name, "  ".join("%+9.1f" % v for v in vals)))

    print("\n== 4. bunnens silhuett: bildet og modellen tilbakeprojisert til modellens silhuettpunkt (plan y = y_sil)")
    bot = E.BOT
    xyz = np.asarray(E._T["bottom_xyz"], float)
    _, rb = E.parts(V, F)
    print("      x   y_sil   z_modell  z_bilde   bilde-modell   (mm; - = bildet dypere)")
    rows = []
    for (u, v), r, (x, y, z) in zip(bot, rb, xyz):
        Xp = hit_plane_y(E.CAM, u, v, y)
        Xm = hit_plane_y(E.CAM, u, v + r, y)
        rows.append((Xm[0], y, Xm[2], Xp[2]))
    rows = np.array(rows)
    o = np.argsort(rows[:, 0])
    rows = rows[o]
    for x0 in range(1000, 2901, 200):
        m = np.abs(rows[:, 0] - x0) < 100
        if m.sum() < 3:
            continue
        print("  %5d  %6.0f  %8.0f  %8.0f   %+6.0f" % (x0, rows[m, 1].mean(), rows[m, 2].mean(), rows[m, 3].mean(),
                                                     (rows[m, 3] - rows[m, 2]).mean()))
    print("  modellens profil (bottom_z) til sammenligning:",
          " ".join("%d:%.0f" % (x, c.C.bottom_z(x)) for x in (1000, 1400, 1800, 2200, 2600, 3000, 3400)))

    print("\n== 5. kjolroten og doedtreet")
    ku, kr = E.keelroot(V, F)
    print("  skrog + kjol mot bildet, per kolonne (modell_v - obs_v):")
    print("   ", " ".join("%d:%+.1f" % (a, b) for a, b in zip(ku[::3], kr[::3])))
    G.use_model(None)
    E._KM = None
    VW, FW = U.hull_mesh(220, 60)
    ku2, kr2 = E.keelroot(VW, FW)
    print("  samme med arbeidstreet (KEEL_LE_FILLET_R %.0f, doedtre fra x %.0f):" % (P.KEEL_LE_FILLET_R,
                                                                                    P.DEADWOOD_H[0][0]))
    print("   ", " ".join("%d:%+.1f" % (a, b) for a, b in zip(ku2[::3], kr2[::3])))
    G.use_model()
    E._KM = None
    # hvor i bildet ligger doedtreets start og kjolens forkant?
    for x, nm in ((2900.0, "doedtreet starter (commit)"), (3154.0, "hulkilens forkant (R 340)"),
                  (3380.0, "kjolens forkant ved roten")):
        z = c.C.bottom_z(x)
        u, v, _ = E.CAM.project(np.array([[x, 0.0, z]]))
        print("  %-30s x %5.0f z %5.0f -> u %5.1f v %5.1f" % (nm, x, z, u[0], v[0]))
    print("  fremre stropp skjuler omrisset u 396-422; bildet viser bunnen flat (v 328-331) til u ~400 og kjolens"
          " forkant fra u ~423.")


if __name__ == "__main__":
    main()
