"""«nye (1)»: den aktre loeftestroppen som spant (14.11.2026).

Brukeren: «Dette bildet med løftestropp må jo avsløre om vi må legge på litt
til.» Stroppen ligger rundt skroget i et tverrplan x = x_s, saa den svarte
streken i bildet er spantet ved x_s sett fra kameraet. Omrisset mot himmelen
(n1_meas.py, trinn 9) dannes av mange spant og er svaert foelsomt for kameraet;
stroppen er ett spant.

  trace   forsoek med dynamisk programmering per kolonne. VIRKET IKKE (fant
          flate linjer); fit bruker i stedet ankerpunktene ANCH_L/ANCH_R,
          lest av i et rutenett, finjustert med refine()
  fit     for hvert kamera i n1_cam.json: x_s med minst rms mellom stroppen og
          modellens projiserte spant, og stroppen tilbakeprojisert paa planet
          x = x_s -> (y, z) mot modellens halvbredder (naa og foer trinn 9).
          Tilbakeprojeksjonen spriker +-15 cm mellom babord og styrbord, saa
          den gir ikke centimeter. Formsammenligningen (skala laast, fri
          flytt/vridning; skriptet laa i scratchpad 14.11) viste stroppen
          utenfor modellen i svingen og litt innenfor ved kjoelen, for fem
          kameraer og x_s 5 600-6 400.
  overlay KAMERA X1,X2,.. FIL   stroppen (groenn) og modellens spant (gult naa,
          cyan foer) over bildet

  python ../../../../tools/memcap.py --gb 3 -- python n1_strap.py trace
  python ../../../../tools/memcap.py --gb 3 -- python n1_strap.py fit [kamera ...]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

import common as c
import n1_geo as N
import opt_mage as M

P, C = N.P, N.C
IMG = c.FOTO + "/nye (1).jpeg"
OUT = c.W + "/out/n1_strap.json"
CAMS = json.load(open(c.W + "/out/n1_cam.json"))
W_, H_ = CAMS["W"], CAMS["H"]


def lum(a):
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def dp_path(cost, v0, lam=4.0, maxstep=3):
    """Billigste sti gjennom kostkartet (rader v, kolonner u) med glatthet."""
    nv, nu = cost.shape
    acc = cost[:, 0].copy()
    back = np.zeros((nv, nu), int)
    for j in range(1, nu):
        best = np.full(nv, np.inf)
        arg = np.zeros(nv, int)
        for s in range(-maxstep, maxstep + 1):
            sh = np.roll(acc, s)
            if s > 0:
                sh[:s] = np.inf
            elif s < 0:
                sh[s:] = np.inf
            cand = sh + lam * abs(s)
            m = cand < best
            best[m] = cand[m]
            arg[m] = (np.arange(nv) - s)[m]
        acc = best + cost[:, j]
        back[:, j] = arg
    k = int(np.argmin(acc))
    path = [k]
    for j in range(nu - 1, 0, -1):
        k = back[k, j]
        path.append(k)
    return np.array(path[::-1]) + v0


def trace():
    a = np.asarray(Image.open(IMG).convert("RGB"), float)
    L = lum(a)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    # stroppen: moerk og graa/svart (ikke roed, ikke blaa himmel)
    dark = L + 0.6 * np.maximum(R - G, 0.0) + 0.8 * np.maximum(B - R, 0.0)
    out = {}
    # (u0, u1, v0, v1, anker-v ved u0 og u1) - grove rammer fra bildet
    for key, (u0, u1, v0, v1) in (("left", (70, 552, 1170, 1660)), ("right", (650, 990, 1360, 1640))):
        sub = dark[v0:v1, u0:u1]
        sub = (sub - np.percentile(sub, 2)) / (np.percentile(sub, 98) - np.percentile(sub, 2) + 1e-9)
        path = dp_path(sub, v0)
        # finjuster: tyngdepunkt av moerket i +-6 px rundt stien
        pts = []
        for j, u in enumerate(range(u0, u1)):
            v = path[j]
            col = dark[v - 7:v + 8, u]
            w = np.maximum(np.percentile(dark[v - 25:v + 26, u], 70) - col, 0.0)
            vv = float(v - 7 + (w * np.arange(15)).sum() / w.sum()) if w.sum() > 0 else float(v)
            pts.append((float(u), vv, float(dark[int(round(vv)), u])))
        out[key] = pts
    json.dump(out, open(OUT, "w"), indent=0)
    im = Image.open(IMG).convert("RGB")
    d = ImageDraw.Draw(im)
    for key in ("left", "right"):
        pts = out[key]
        d.line([(u, v) for u, v, _ in pts], fill=(0, 255, 0), width=1)
    im.crop((0, 1100, 1170, 1900)).save(c.W + "/out/n1_strap_trace.png")
    print("spor:", {k: len(v) for k, v in out.items()}, "->", OUT)


# Stroppens midtlinje lest av i 2x-rutenett (fullt bilde 1170 x 2532), u -> v.
# Venstre = babord (-y), hoeyre = styrbord. Mellom u 552 og 640 skjuler
# propellen stroppen. Oeverst til venstre (u < 70) ligger stroppen i omrisset.
ANCH_L = [(70, 1392), (85, 1410), (100, 1421), (125, 1437), (150, 1450), (200, 1473), (250, 1495),
          (300, 1518), (350, 1540), (400, 1560), (450, 1580), (500, 1600), (550, 1622)]
ANCH_R = [(645, 1592), (700, 1574), (750, 1548), (800, 1527), (850, 1507), (900, 1491), (950, 1462),
          (975, 1442), (990, 1424), (1000, 1405)]


def refine(anch, step=4, half=9):
    """Moerkeste punkt (glattet) loddrett innenfor +-half px fra ankerlinja."""
    a = np.asarray(Image.open(IMG).convert("RGB"), float)
    L = lum(a)
    A = np.asarray(anch, float)
    out = []
    for u in np.arange(A[0, 0], A[-1, 0] + 0.1, step):
        v0 = np.interp(u, A[:, 0], A[:, 1])
        ui = int(round(u))
        vs = np.arange(int(v0) - half, int(v0) + half + 1)
        col = np.convolve(L[vs.min() - 2:vs.max() + 3, ui - 1:ui + 2].mean(1), np.ones(5) / 5.0, mode="valid")
        k = int(np.argmin(col))
        # parabel rundt minimum
        if 0 < k < len(col) - 1:
            d = col[k - 1] - 2 * col[k] + col[k + 1]
            off = 0.5 * (col[k - 1] - col[k + 1]) / d if d > 1e-9 else 0.0
        else:
            off = 0.0
        out.append((float(u), float(vs[k] + off), float(col[k])))
    return np.array(out)


def strap_pts():
    return refine(ANCH_L), refine(ANCH_R)


def install(which):
    if which == "naa":
        M.install(np.r_[P.BELLY_DEADRISE, P.BELLY_N, P.BELLY_FLARE].astype(float))
    else:
        M.install(np.zeros(3 * len(M.KNOTS)))


def section3d(x, side, n=240):
    s = np.asarray(C.section(float(x), n), float)          # K -> D, y >= 0
    return np.c_[np.full(len(s), float(x)), side * s[:, 0], s[:, 1]]


def poly_dist(Q, Puv):
    """Avstand fra hvert punkt i Q (n,2) til polylinja Puv (m,2), med fortegn
    (+ = paa den siden som vender bort fra polylinjas venstre normal)."""
    A, B = Puv[:-1], Puv[1:]
    AB = B - A
    L2 = (AB ** 2).sum(1) + 1e-12
    out = np.zeros(len(Q))
    for i, q in enumerate(Q):
        t = np.clip(((q - A) * AB).sum(1) / L2, 0.0, 1.0)
        Pp = A + t[:, None] * AB
        d = np.sqrt(((q - Pp) ** 2).sum(1))
        j = int(np.argmin(d))
        cr = AB[j, 0] * (q[1] - A[j, 1]) - AB[j, 1] * (q[0] - A[j, 0])
        out[i] = d[j] * np.sign(cr)
    return out


def back_project(cam, uv, x_s):
    """Strale gjennom (u, v) skaaret med planet x = x_s -> (y, z)."""
    d = cam.ray(uv[:, 0], uv[:, 1])
    t = (x_s - cam.C[0]) / d[:, 0]
    X = cam.C[None, :] + t[:, None] * d
    return X[:, 1], X[:, 2]


def half_breadth_at(x, zs, n=600):
    s = np.asarray(C.section(float(x), n), float)
    out = []
    for z in zs:
        i = np.where((s[:-1, 1] - z) * (s[1:, 1] - z) <= 0)[0]
        ys = [s[k, 0] + (z - s[k, 1]) / (s[k + 1, 1] - s[k, 1]) * (s[k + 1, 0] - s[k, 0])
              for k in i if s[k + 1, 1] != s[k, 1]]
        out.append(max(ys) if ys else np.nan)
    return np.array(out)


def fit(variants):
    SL, SR = strap_pts()
    res = {}
    xs = np.arange(5000.0, 6801.0, 50.0)
    for var in variants:
        m = CAMS["modes"][var]
        cam = N.make_cam(np.array(m["q"]), m["mode"], W_, H_)
        # senterlinjen: laveste punkt paa stroppen (u ~ 560-640 skjult; ta skjaering av
        # de to rette bunnlinjene) -> straale -> planet y = 0
        rows = {}
        for which in ("naa", "foer"):
            install(which)
            rr = []
            for x in xs:
                pl = np.c_[cam.project(section3d(x, -1.0))[:2]]
                pr = np.c_[cam.project(section3d(x, 1.0))[:2]]
                dl = poly_dist(SL[:, :2], pl)
                dr = poly_dist(SR[:, :2], pr)
                rr.append((x, dl, dr))
            rows[which] = rr
        # x_s: best samlet passform for den naavaerende modellen (hele stroppen)
        tot = [np.sqrt(np.mean(np.r_[dl, dr] ** 2)) for _, dl, dr in rows["naa"]]
        k = int(np.argmin(tot))
        res[var] = dict(cost=m["cost"], x_best=float(xs[k]), rms_best=float(tot[k]),
                        rms_curve=[float(t) for t in tot])
        print(f"\n== {var} (kamerakost {m['cost']:.0f}): beste x_s {xs[k]:.0f} (rms {tot[k]:.1f} px)")
        print("   x_s:  " + " ".join(f"{x:5.0f}" for x in xs[::2]))
        print("   rms:  " + " ".join(f"{t:5.1f}" for t in tot[::2]))
        # tilbakeprojeksjon paa x_s og naboer: bildets spant mot modellens
        zs = np.array([-500.0, -400.0, -300.0, -200.0, -100.0, 0.0, 100.0, 200.0])
        for xx in (xs[k] - 200.0, xs[k], xs[k] + 200.0):
            install("naa")
            yl, zl = back_project(cam, SL[:, :2], xx)
            yr, zr = back_project(cam, SR[:, :2], xx)
            hb_naa = half_breadth_at(xx, zs)
            install("foer")
            hb_foer = half_breadth_at(xx, zs)
            line = []
            for z, hn, hf in zip(zs, hb_naa, hb_foer):
                def at(yy, zz):
                    o = np.argsort(zz)
                    return np.interp(z, zz[o], np.abs(yy[o]), left=np.nan, right=np.nan)
                pl_, pr_ = at(yl, zl), at(yr, zr)
                line.append(f"z{z:5.0f}: bilde B {pl_:5.0f} S {pr_:5.0f} | naa {hn:5.0f} foer {hf:5.0f}")
            print(f"   x_s {xx:5.0f}: halvbredde (mm), bildet tilbakeprojisert mot modellen")
            for s in line:
                print("     " + s)
            print(f"     stroppens laveste punkt: z {min(zl.min(), zr.min()):.0f}; modellens kjoelpunkt K:"
                  f" z {C.section(float(xx), 10)[0][1]:.0f}")
    json.dump(res, open(c.W + "/out/n1_strap_fit.json", "w"), indent=1)


def overlay(var, xs_list, path):
    m = CAMS["modes"][var]
    cam = N.make_cam(np.array(m["q"]), m["mode"], W_, H_)
    im = Image.open(IMG).convert("RGB")
    d = ImageDraw.Draw(im)
    SL, SR = strap_pts()
    for S_ in (SL, SR):
        d.line([(u, v) for u, v, _ in S_], fill=(0, 255, 0), width=3)
    cols = {"naa": (255, 255, 0), "foer": (0, 200, 255)}
    for which in ("foer", "naa"):
        install(which)
        for x in xs_list:
            for side in (-1.0, 1.0):
                u, v, _ = cam.project(section3d(x, side))
                d.line(list(zip(u, v)), fill=cols[which], width=2)
    install("naa")
    im.crop((0, 1050, 1170, 1950)).save(path)


if __name__ == "__main__":
    if sys.argv[1] == "trace":
        trace()
    elif sys.argv[1] == "fit":
        fit(sys.argv[2:] or ["ppk12", "ppk1_kdz", "ppk1_corn", "ppk12_corn", "ppk1", "pp_nok", "pp_corn", "pp"])
    elif sys.argv[1] == "overlay":
        var = sys.argv[2]
        xs_ = [float(a) for a in sys.argv[3].split(",")]
        overlay(var, xs_, sys.argv[4])
