"""Restfunksjoner for forkroppen under vann i IMG_9387 (babord side paa land).

  CAM            uwlib.Cam fra ../out/cam9387.json (loest uten forkroppen)
  resid(V, F)    fortegnsriktige px-rester for omrisset foran kjolen,
                 positivt = modellen ligger UTENFOR bildets omriss:
                   front  (per bilderad, rad 540-690): obs_u - modell_u
                          (stevn og forfot; modellen lenger forut = +)
                   bottom (per bildekolonne): modell_v - obs_v
                          (bunnens silhuett; modellen dypere/fyldigere = +)
                 Rader/kolonner der kjol, ror, stativ eller roer danner eller
                 skjuler omrisset er tatt ut (fk9387.py).
  resid_bt(V, F) stripens nedre kant (lys -> roedt) forut for x 3 800:
                 modell_v - obs_v for modellens linje z_red(x) paa skroget
                 (planet snitter nettet, babord side). NB: kameraet staar i
                 omtrent samme hoeyde som linja, saa den er nesten
                 ufoelsom for halvbredden (~0,5 px per 100 mm); den er en
                 kontroll, ikke et formmaal.
  keelroot(V, F) kjolroten (ikke i resid): skrog + kjol mot bildets hulkil,
                 rad 800-860 (obs_u - modell_u) og kolonner foran (modell_v - obs_v)
  summary(V, F)  middel/rms per region, i px og omtrent mm.

V, F: et hvilket som helst analytisk skrognett uten kjol og ror, f.eks.
photos.mesh() (= uwlib.hull_mesh(220, 60)). resid tar ca. 0,01 s, resid_bt
ca. 0,05-0,15 s. Foelsomhet (vurder9387.py): bunnen 20 mm dypere -> +6,6 px,
bunnen 50 mm bredere -> +0,6 px (bildet maaler dybden, ikke spantformen),
forfoten 20 mm forover -> +9,9 px paa front.
"""
import json
import time

import numpy as np

import common as c
import uwlib as U

_CJ = json.load(open(c.W + "/out/cam9387.json"))
CAM = U.Cam(_CJ["p"], 2000, 1500)
_T = json.load(open(c.W + "/out/t9387_forkropp.json"))
FRONT = np.asarray(_T["front"], float)          # [v, u]
BOT = np.asarray(_T["bottom"], float)           # [u, v]
BTR = np.asarray(_T["bt_red"], float)           # [u, v]
FRONT_X = np.asarray(_T["front_x"], float)
BOT_X = np.asarray(_T["bottom_x"], float)
FRONT_MMPX = np.asarray(_T["front_mmpx"], float)
BOT_MMPX = np.asarray(_T["bottom_mmpx"], float)
DZR, KS = _CJ["bt_dz_red"], _CJ["bt_slope_per_m"]
X_MAX = 5200.0          # flater lenger akter kan ikke danne forkroppens omriss her
Z_MAX = 700.0
CAP = 40.0              # rest naar modellen ikke naar raden/kolonnen i det hele tatt


def z_red(x):
    """Stripens nedre kant paa skroget med dette kameraet (se cam9387.py)."""
    return 38.0 + DZR + KS * (np.asarray(x, float) - 4000.0) / 1000.0


def _faces(V, F):
    Vf = V[F]
    keep = (Vf[:, :, 0].min(1) < X_MAX) & (Vf[:, :, 2].min(1) < Z_MAX)
    return F[keep]


def parts(V, F):
    Fk = _faces(V, F)
    lo, _ = U.row_extents(CAM, V, Fk, FRONT[:, 0])
    rf = np.where(np.isfinite(lo), FRONT[:, 1] - lo, -CAP)
    _, hi = U.row_extents(CAM, V, Fk, BOT[:, 0], axis="col")
    rb = np.where(np.isfinite(hi), hi - BOT[:, 1], -CAP)
    return rf, rb


def resid(V, F):
    rf, rb = parts(V, F)
    return np.r_[rf, rb]


def _zline(V, F, zfun, xmax=3900.0):
    """Skjaering mellom nettet og flaten z = zfun(x) paa babord side (y < -5)."""
    E = np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]
    E = np.sort(E, axis=1)
    E = np.unique(E, axis=0)
    A, B = V[E[:, 0]], V[E[:, 1]]
    ha = A[:, 2] - zfun(A[:, 0])
    hb = B[:, 2] - zfun(B[:, 0])
    m = (ha * hb < 0) & (np.minimum(A[:, 0], B[:, 0]) < xmax) & (np.maximum(A[:, 1], B[:, 1]) < -5.0)
    t = ha[m] / (ha[m] - hb[m])
    return A[m] + t[:, None] * (B[m] - A[m])


_EDGES = {}


def resid_bt(V, F):
    """Stripens nedre kant forut: modell_v - obs_v (positivt = modellens linje
    lavere i bildet enn fotoets)."""
    X = _zline(V, F, z_red)
    if len(X) < 3:
        return np.full(len(BTR), CAP)
    u, v, d = CAM.project(X)
    o = np.argsort(u)
    u, v = u[o], v[o]
    inside = (BTR[:, 0] >= u[0]) & (BTR[:, 0] <= u[-1])
    pred = np.interp(BTR[:, 0], u, v)
    return np.where(inside, pred - BTR[:, 1], CAP)


_KM = None


def keelroot(V, F):
    """Kjolroten (ikke i resid): modellens omriss med kjolen (geo9387.keel_mesh,
    hulkil etter A._KeelProfile) mot bildet. Per rad 800-860: obs_u - modell_u
    (+ = modellen lenger forut); per kolonne: modell_v - obs_v (+ = dypere)."""
    global _KM
    if _KM is None:
        import geo9387 as G
        _KM = G.keel_mesh()
    VK, FK = _KM
    rr = np.asarray(_T["root_rows"], float)
    rc = np.asarray(_T["root_cols"], float)
    Fk = _faces(V, F)
    lo_h, _ = U.row_extents(CAM, V, Fk, rr[:, 0])
    lo_k, _ = U.row_extents(CAM, VK, FK, rr[:, 0])
    lo = np.fmin(lo_h, lo_k)
    _, hi_h = U.row_extents(CAM, V, Fk, rc[:, 0], axis="col")
    _, hi_k = U.row_extents(CAM, VK, FK, rc[:, 0], axis="col")
    hi = np.fmax(hi_h, hi_k)
    return rr[:, 1] - lo, hi - rc[:, 1]


REGIONS = [("front: stevn over z~120 (rad 540-615)", "f", lambda: FRONT[:, 0] <= 615),
           ("front: forfot z~120..-30 (rad 616-690)", "f", lambda: FRONT[:, 0] > 615),
           ("bunn x 1000-1500", "b", lambda: BOT_X < 1500),
           ("bunn x 1500-2000", "b", lambda: (BOT_X >= 1500) & (BOT_X < 2000)),
           ("bunn x 2000-2400", "b", lambda: (BOT_X >= 2000) & (BOT_X < 2400)),
           ("bunn x 2400-3000 (u 862-937)", "b", lambda: BOT_X >= 2400)]


def summary(V, F, tag=""):
    t0 = time.time()
    rf, rb = parts(V, F)
    dt = time.time() - t0
    rbt = resid_bt(V, F)
    lines = []
    for name, kind, sel in REGIONS:
        m = sel()
        r = rf[m] if kind == "f" else rb[m]
        mm = (FRONT_MMPX[m] if kind == "f" else BOT_MMPX[m]) * r
        if len(r) == 0:
            continue
        lines.append("  %-40s n %3d  middel %+6.1f px (%+5.0f mm)  rms %5.1f px (%4.0f mm)  maks %+6.1f px"
                     % (name, len(r), r.mean(), mm.mean(), np.sqrt(np.mean(r ** 2)), np.sqrt(np.mean(mm ** 2)),
                        r[np.argmax(np.abs(r))]))
    ok = rbt != CAP
    lines.append("  %-40s n %3d  middel %+6.1f px  rms %5.1f px (kontroll, nesten ufoelsom for formen)"
                 % ("stripens nedre kant forut", ok.sum(), rbt[ok].mean() if ok.any() else np.nan,
                    np.sqrt(np.mean(rbt[ok] ** 2)) if ok.any() else np.nan))
    allr = np.r_[rf, rb]
    print("IMG_9387 forkropp %s: alle n %d middel %+.1f rms %.1f px (+ = modellen utenfor bildets omriss)  [%.2f s]"
          % (tag, len(allr), allr.mean(), np.sqrt(np.mean(allr ** 2)), dt))
    print("\n".join(lines), flush=True)
    return dict(front=rf, bottom=rb, bt=rbt)


if __name__ == "__main__":
    import photos
    V, F = photos.mesh()
    t0 = time.time()
    r = resid(V, F)
    t1 = time.time()
    print("resid: %d rester, %.3f s" % (len(r), t1 - t0))
    summary(V, F, "dagens modell")
