"""Restfunksjoner for forkroppen under vann i IMG_9374 (babord side, baaten i
stroppene i travelliften, 761 x 472).

  CAM            geo9374.Cam9374 (en uwlib.Cam med radial fortegning k1) fra
                 ../out/cam9374.json, hovedkameraet 'k1_bt' (loest uten
                 forkroppen: fenderlist, stevn over z +300, vindu, kjol,
                 stripen aktenfor x 3 800)
  resid(V, F)    fortegnsriktige px-rester for omrisset foran kjolen,
                 positivt = modellen ligger UTENFOR bildets omriss:
                   front  (per bilderad, rad ~251-283): obs_u - modell_u
                          (stevn under z +300 og forfot; modellen lenger forut = +)
                   bottom (per bildekolonne, u 167-377): modell_v - obs_v
                          (bunnens silhuett; modellen dypere/fyldigere = +)
                 Kolonner der kjolen (med hulkil) danner omrisset, og der den
                 fremre stroppen krysser, er tatt ut (fk9374.py).
  resid_bt(V, F) nedre kant av den lyse stripen (lys -> roedt) forut for
                 x 3 800: modell_v - obs_v for modellens linje z_red(x) paa
                 skroget (planet snitter nettet, babord side). Kameraet staar
                 nesten i hoeyde med linja, saa den er lite foelsom for
                 halvbredden; den er en kontroll, ikke et formmaal.
  keelroot(V, F) kontroll (ikke i resid): skrog + kjol mot bildets omriss
                 der bunnen gaar over i kjolens forkant (u 378-396 og 423-445).
  summary(V, F)  middel/rms per region, i px og omtrent mm.

Om kameraet (se cam9374.py): et rent hullkamera (uwlib.Cam, 7 parametre)
klarer ikke fenderlist, stevn og kjol samtidig (U-formet rest paa listen,
+-5 px, stevnens vinkel 2-4 px feil, og med fri kjol vil det flytte kjolen
290 mm ned). Med radial fortegning k1 (+0,27) passer alt innen 0,4-1,5 px,
og dekkskanten (ikke brukt i tilpasningen) blir en jevn forskyvning
(rekka) i stedet for en skraa rest. Andre kameraer som ogsaa passer
(fritt hovedpunkt + k1, k1 + pikselforhold) gir samme forkropps-rester
innen ca. 1 px. Et rent hullkamera gir 3 px mindre negativ bunn: se
summary(..., alt=True).

V, F: et hvilket som helst analytisk skrognett uten kjol og ror, f.eks.
photos.mesh() (= uwlib.hull_mesh(220, 60)). resid tar ca. 0,01 s. resid og
resid_bt bruker ikke modellen ellers (kamera og spor er tall i JSON), saa de
kan kalles med hovedoektas nett midt i en tilpasning. keelroot bygger kjolen
fra hr26 slik modulen er lastet.

Foelsomhet (vurder9374.py): bunnen 20 mm dypere -> +2,3..2,5 px, 50 mm
bredere -> +0,1 px, slaget (|y| > 300) 30 mm ned -> 0 px: bildet maaler
bunnens dybde innen ca. +-300 mm fra senterlinjen, ikke bredde, bunnreisning
eller slag. Forfoten 20 mm forover -> +2,9 px paa front.

Dagens modell (commit 0976477, kamera k1_bt): front +3,9 px (forfoten ca.
30 mm for langt forut), bunn x 0,9-1,3 m +0,9, 1,3-1,8 m -3,7, 1,8-2,3 m -5,1,
2,3-2,9 m -4,8 px (bunnen 30-45 mm for hoey).
"""
import json
import time

import numpy as np

import common as c
import uwlib as U
import geo9374 as G

CAM, _CD = G.load_cam()
_CJ = json.load(open(c.W + "/out/cam9374.json"))
_T = json.load(open(c.W + "/out/t9374_forkropp.json"))
FRONT = np.asarray(_T["front"], float)          # [v, u]
BOT = np.asarray(_T["bottom"], float)           # [u, v]
BTR = np.asarray(_T["bt_red"], float)           # [u, v]
FRONT_X = np.asarray(_T["front_x"], float)
BOT_X = np.asarray(_T["bottom_x"], float)
FRONT_MMPX = np.asarray(_T["front_mmpx"], float)
BOT_MMPX = np.asarray(_T["bottom_mmpx"], float)
DZR, KS = _CJ["bt_dz_red"], _CJ["bt_slope_per_m"]
X_MAX = 5000.0          # flater lenger akter kan ikke danne forkroppens omriss her
Z_MAX = 600.0
CAP = 40.0              # rest naar modellen ikke naar raden/kolonnen i det hele tatt


def z_red(x):
    """Stripens nedre kant paa skroget med dette kameraet (se cam9374.py)."""
    return 38.0 + DZR + KS * (np.asarray(x, float) - 4000.0) / 1000.0


def _faces(V, F):
    Vf = V[F]
    keep = (Vf[:, :, 0].min(1) < X_MAX) & (Vf[:, :, 2].min(1) < Z_MAX)
    return F[keep]


def extents(cam, V, F, pos, axis="row", step=0.5):
    """uwlib.row_extents paa et JEVNT rutenett (row_extents krever jevnt
    fordelte rader/kolonner) og avlest i pos (som kan ha hull)."""
    pos = np.asarray(pos, float)
    a, b = np.floor(pos.min()), np.ceil(pos.max())
    grid = np.arange(a, b + 0.5 * step, step)
    lo, hi = U.row_extents(cam, V, F, grid, axis=axis)
    k = np.clip(np.round((pos - a) / step).astype(int), 0, len(grid) - 1)
    exact = np.abs(grid[k] - pos) < 1e-6
    if exact.all():
        return lo[k], hi[k]
    def itp(y):
        ok = np.isfinite(y)
        out = np.full(len(pos), np.nan)
        if ok.sum() >= 2:
            out = np.interp(pos, grid[ok], y[ok], left=np.nan, right=np.nan)
        return np.where(exact, y[k], out)
    lo2, hi2 = itp(lo), itp(hi)
    return np.where(np.isfinite(lo2), lo2, np.inf), np.where(np.isfinite(hi2), hi2, -np.inf)


def parts(V, F, cam=None):
    cam = CAM if cam is None else cam
    Fk = _faces(V, F)
    lo, _ = extents(cam, V, Fk, FRONT[:, 0], step=1.0)
    rf = np.where(np.isfinite(lo), FRONT[:, 1] - lo, -CAP)
    _, hi = extents(cam, V, Fk, BOT[:, 0], axis="col", step=1.0)
    rb = np.where(np.isfinite(hi), hi - BOT[:, 1], -CAP)
    return rf, rb


def resid(V, F):
    rf, rb = parts(V, F)
    return np.r_[rf, rb]


def _zline(V, F, zfun, xmax=3900.0):
    """Skjaering mellom nettet og flaten z = zfun(x) paa babord side (y < -5)."""
    E = np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]
    E = np.unique(np.sort(E, axis=1), axis=0)
    A, B = V[E[:, 0]], V[E[:, 1]]
    ha = A[:, 2] - zfun(A[:, 0])
    hb = B[:, 2] - zfun(B[:, 0])
    m = (ha * hb < 0) & (np.minimum(A[:, 0], B[:, 0]) < xmax) & (np.maximum(A[:, 1], B[:, 1]) < -5.0)
    t = ha[m] / (ha[m] - hb[m])
    return A[m] + t[:, None] * (B[m] - A[m])


def resid_bt(V, F, cam=None):
    """Stripens nedre kant forut: modell_v - obs_v (positivt = modellens linje
    lavere i bildet enn fotoets)."""
    cam = CAM if cam is None else cam
    X = _zline(V, F, z_red)
    if len(X) < 3:
        return np.full(len(BTR), CAP)
    u, v, d = cam.project(X)
    o = np.argsort(u)
    u, v = u[o], v[o]
    inside = (BTR[:, 0] >= u[0]) & (BTR[:, 0] <= u[-1])
    pred = np.interp(BTR[:, 0], u, v)
    return np.where(inside, pred - BTR[:, 1], CAP)


_KM = None
_ROOT = None


def keelroot(V, F, cam=None):
    """Kontroll (ikke i resid): modellens omriss med kjolen (geo9374.keel_mesh,
    hulkil etter A._KeelProfile) mot bildets nederste roede rad i kolonnene
    rundt kjolens forkant: modell_v - obs_v (+ = modellen lavere)."""
    global _KM, _ROOT
    cam = CAM if cam is None else cam
    if _KM is None:
        _KM = G.keel_mesh()
        raw = np.asarray(json.load(open(c.W + "/out/t9374_raw.json"))["bottom"], float)
        m = ((raw[:, 0] >= 378) & (raw[:, 0] <= 396)) | ((raw[:, 0] >= 423) & (raw[:, 0] <= 445))
        _ROOT = raw[m]
    VK, FK = _KM
    Fk = _faces(V, F)
    _, hh = extents(cam, V, Fk, _ROOT[:, 0], axis="col", step=1.0)
    _, hk = extents(cam, VK, FK, _ROOT[:, 0], axis="col", step=1.0)
    return _ROOT[:, 0], np.fmax(hh, hk) - _ROOT[:, 1]


REGIONS = [("front: stevn/forfot z ~ +300..+60 (rad 251-283)", "f", lambda: np.ones(len(FRONT), bool)),
           ("bunn x  900-1300 (forfoten)", "b", lambda: BOT_X < 1300),
           ("bunn x 1300-1800", "b", lambda: (BOT_X >= 1300) & (BOT_X < 1800)),
           ("bunn x 1800-2300", "b", lambda: (BOT_X >= 1800) & (BOT_X < 2300)),
           ("bunn x 2300-2900 (til kjolens hulkil)", "b", lambda: BOT_X >= 2300)]


def _line(name, r, mmpx):
    if len(r) == 0:
        return "  %-42s n   0" % name
    mm = mmpx * r
    return ("  %-42s n %3d  middel %+6.1f px (%+5.0f mm)  rms %5.1f px (%4.0f mm)  maks %+6.1f px"
            % (name, len(r), r.mean(), mm.mean(), np.sqrt(np.mean(r ** 2)), np.sqrt(np.mean(mm ** 2)),
               r[np.argmax(np.abs(r))]))


def summary(V, F, tag="", alt=False):
    """Middel/rms per region. alt=True: ogsaa med de andre kameraene i
    cam9374.json (hvor mye kameravalget flytter tallene)."""
    t0 = time.time()
    rf, rb = parts(V, F)
    dt = time.time() - t0
    rbt = resid_bt(V, F)
    lines = []
    for name, kind, sel in REGIONS:
        m = sel()
        lines.append(_line(name, rf[m] if kind == "f" else rb[m], FRONT_MMPX[m] if kind == "f" else BOT_MMPX[m]))
    ok = rbt != CAP
    lines.append("  %-42s n %3d  middel %+6.1f px  rms %5.1f px (kontroll, lite foelsom for formen)"
                 % ("stripens nedre kant forut (x < 3800)", ok.sum(), rbt[ok].mean() if ok.any() else np.nan,
                    np.sqrt(np.mean(rbt[ok] ** 2)) if ok.any() else np.nan))
    ku, kr = keelroot(V, F)
    lines.append("  %-42s n %3d  middel %+6.1f px  (u 378-396: %+.1f, u 423-445: %+.1f)"
                 % ("kontroll: kjolroten (skrog + kjol)", len(kr), np.nanmean(kr), np.nanmean(kr[ku <= 396]),
                    np.nanmean(kr[ku >= 423])))
    allr = np.r_[rf, rb]
    print("IMG_9374 forkropp %s: alle n %d middel %+.1f rms %.1f px (+ = modellen utenfor bildets omriss)  [%.3f s]"
          % (tag, len(allr), allr.mean(), np.sqrt(np.mean(allr ** 2)), dt))
    print("\n".join(lines), flush=True)
    if alt:
        print("  andre kameraer (middel px: front | bunn per x-region):")
        for m in ("k1_bt", "ppk1_bt", "k1asp_bt", "pp_bt", "pin_bt"):
            if m not in _CJ["modes"]:
                continue
            cam, _ = G.load_cam(m)
            a, b = parts(V, F, cam)
            s = " ".join("%+5.1f" % b[sel()].mean() for _, kind, sel in REGIONS if kind == "b")
            print("    %-9s front %+5.1f | bunn %s   (kamera-rms liste %.2f stevn %.2f kjol %.2f/%.2f/%.2f)"
                  % (m, a.mean(), s, _CJ["modes"][m]["rms"]["strake"], _CJ["modes"][m]["rms"]["stem"],
                     _CJ["modes"][m]["rms"]["keel_le"], _CJ["modes"][m]["rms"]["keel_te"],
                     _CJ["modes"][m]["rms"]["keel_bot"]))
    return dict(front=rf, bottom=rb, bt=rbt)


if __name__ == "__main__":
    import photos
    G.use_model()                       # modellen eieren saa (commit G.MODEL_REV, foer trinn 5)
    V, F = photos.mesh()
    t0 = time.time()
    for _ in range(5):
        r = resid(V, F)
    t1 = time.time()
    print("resid: %d rester, %.4f s per kall" % (len(r), (t1 - t0) / 5))
    summary(V, F, "commit " + G.MODEL_REV, alt=True)
    G.use_model(None)                   # arbeidstreet slik det ligger naa
    _KM = None
    V, F = photos.mesh()
    summary(V, F, "arbeidstreet")
