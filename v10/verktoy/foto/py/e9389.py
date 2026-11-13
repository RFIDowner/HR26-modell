"""Restfunksjoner for forkroppen under vann i IMG_9389 (3/4 forfra styrbord,
paa land; kamera ca. 2,2 m ut til styrbord, 0,1 m foran stevnen, ca. 105 mm
over DWL (ca. 1,6 m over bakken), ser ned ca. 10,6 grader, f 1 543 px).

  CAM            uwlib.Cam fra ../out/cam9389.json (variant 'stripe', loest uten
                 forkroppens omriss: fenderlist, kjol under hulkilen, venstre
                 omriss, hele vannlinjestripen med fri hoeyde; se cam9389.py)
  resid(V, F)    fortegnsriktige px-rester, positivt = modellen ligger UTENFOR
                 bildets omriss. 251 rester = [bottom (207), front (44)]:
                   bottom (per bildekolonne u 1095-1890): modell_v - obs_v.
                          Omrisset dannes av kjollinja/bunnen innen ca. 170 mm
                          fra senterlinjen, x ca. 1 000-2 600, z -350..0, sett
                          litt ovenfra: bildet maaler DYBDEN der (0,5-0,65 px
                          per mm), svakt bunnreisningen (5 grader flatere ->
                          +5..+9 px ved x 1 500-2 600) og nesten ikke fylden
                          (10 % bredere under DWL -> < 1 px).
                   front  (per bilderad v 352-440): modell_u - obs_u, forfoten/
                          stevnen ved x ca. 870-990, z +20..+120 (modellen
                          lenger forut/ut = +).
                 Kolonner der kjolen (med hulkil) danner eller naermer seg
                 omrisset (innen 12 px) tas ut ved import (0 med dagens kamera).
                 Kameraets usikkerhet (f +-25 px) flytter restene: front +-26 px,
                 bunn x<1500 +-13, 1500-2000 +-8, 2000-2600 +-5 (prof9389.py).
                 Foreslaatt vekt: front sigma 15 px, bunn x<1500 8 px, ellers 5 px.
  resid_bt(V, F) stripens nedre kant (lys -> roedt) forut for x 4 600:
                 modell_v - obs_v for linja z = 38 + bt_dz_red + k (x-4000)/1000
                 paa styrbord side. Kameraet staar nesten i hoeyde med linja,
                 saa den er nesten ufoelsom for spantformen (0 px for endringene
                 i sens9389.py); den er en kontroll av kameraet, ikke et formmaal.
                 Stripen forut er med i kameraet, saa den er ca. 0 her.
  summary(V, F)  middel/rms per region, i px og omtrent mm.
  outline_points(V, F)  3D-punktene paa modellen som danner omrisset (diagnose).
  set_cam(p, dzr, dzt, k)  bytt kamera (variantene i cam9389.json['variants']).

V, F: et hvilket som helst analytisk skrognett uten kjol og ror, f.eks.
photos.mesh() (= uwlib.hull_mesh(220, 60)). resid tar ca. 0,01 s.
"""
import json
import time

import numpy as np

import common as c
import uwlib as U

_CJ = json.load(open(c.W + "/out/cam9389.json"))
CAM = U.Cam(_CJ["p"], 2000, 1500)
DZR = float(_CJ["bt_dz_red"])
DZT = float(_CJ["bt_dz_top"])
KBT = float(_CJ.get("bt_slope_per_m", 0.0))     # stripens helning, mm per m
_T = json.load(open(c.W + "/out/t9389_forkropp.json"))
BOT_ALL = np.asarray(_T["bottom"], float)        # [u, v]
FRONT = np.asarray(_T["front"], float)           # [v, u]
BTR_ALL = np.asarray(_T["bt_red"], float)        # [u, v]
BTT_ALL = np.asarray(_T["bt_top"], float)        # [u, v]
X_MAX = 5000.0          # flater lenger akter kan ikke danne forkroppens omriss her
Z_MAX = 400.0
CAP = 40.0              # rest naar modellen ikke naar raden/kolonnen i det hele tatt
KEEL_MARGIN = 12.0      # px: kolonner der kjolens nedre kant er mindre enn dette over omrisset tas ut


def _keel_mask():
    """Kolonner der kjolen (A._KeelProfile med hulkil, 240 mm) ikke danner
    eller naermer seg omrisset med dette kameraet."""
    import geo9389 as G
    VK, FK = G.keel_mesh()
    _, hk = U.row_extents(CAM, VK, FK, BOT_ALL[:, 0], axis="col")
    ok = ~np.isfinite(hk) | (hk < BOT_ALL[:, 1] - KEEL_MARGIN)
    return ok, hk


_KOK, _KEEL_V = _keel_mask()
BOT = BOT_ALL[_KOK]


def set_cam(p, dzr=None, dzt=None, k=None):
    """Bytter kamera (til foelsomhetsstudier): masker og stripegrense regnes paa nytt."""
    global CAM, DZR, DZT, KBT, _KOK, _KEEL_V, BOT, BT_ULIM, BTR, BTT
    CAM = U.Cam(p[:7], 2000, 1500)
    KBT = float(k) if k is not None else 0.0
    if dzr is not None:
        DZR = float(dzr)
    if dzt is not None:
        DZT = float(dzt)
    _KOK, _KEEL_V = _keel_mask()
    BOT = BOT_ALL[_KOK]
    BT_ULIM = _bt_ulim()
    BTR = BTR_ALL[BTR_ALL[:, 0] >= BT_ULIM + 5.0]
    BTT = BTT_ALL[BTT_ALL[:, 0] >= BT_ULIM + 5.0]
    _DIAG.clear()


def _bt_ulim(xmax=4600.0):
    import geo9389 as G
    X = G.zline3(lambda x: 38.0 + DZR + KBT * (x - 4000.0) / 1000.0, xmax, xmax + 1.0, 2)
    return float(CAM.project(X[:1])[0][0])


BT_ULIM = _bt_ulim()
BTR = BTR_ALL[BTR_ALL[:, 0] >= BT_ULIM + 5.0]    # bare stripen forut for x 4 600
BTT = BTT_ALL[BTT_ALL[:, 0] >= BT_ULIM + 5.0]


def _faces(V, F):
    Vf = V[F]
    keep = (Vf[:, :, 0].min(1) < X_MAX) & (Vf[:, :, 2].min(1) < Z_MAX)
    return F[keep]


def parts(V, F):
    Fk = _faces(V, F)
    _, hi = U.row_extents(CAM, V, Fk, BOT[:, 0], axis="col")
    rb = np.where(np.isfinite(hi), hi - BOT[:, 1], -CAP)
    _, hu = U.row_extents(CAM, V, Fk, FRONT[:, 0])
    rf = np.where(np.isfinite(hu), hu - FRONT[:, 1], -CAP)
    return rb, rf


def resid(V, F):
    rb, rf = parts(V, F)
    return np.r_[rb, rf]


# ---------------------------------------------------------------- 3D-punktene paa omrisset
def _crossings(cam, V, F, lines, axis):
    """Alle kryssinger mellom projiserte trekantkanter og bildelinjene:
    (indeks, koordinat langs linja, 3D-punkt)."""
    u, v, z = cam.project(V)
    if axis == "col":
        u, v = v, u
    ok = (z[F] > 150.0).all(1)
    Fk = F[ok]
    lines = np.asarray(lines, float)
    out_k, out_c, out_X = [], [], []
    for e0, e1 in ((0, 1), (1, 2), (2, 0)):
        a, b = Fk[:, e0], Fk[:, e1]
        wa, wb = v[a], v[b]
        for k, L in enumerate(lines):
            m = (np.minimum(wa, wb) <= L) & (np.maximum(wa, wb) > L)
            if not m.any():
                continue
            t = (L - wa[m]) / (wb[m] - wa[m])
            cc = u[a[m]] + t * (u[b[m]] - u[a[m]])
            X = V[a[m]] + t[:, None] * (V[b[m]] - V[a[m]])
            out_k.append(np.full(m.sum(), k)); out_c.append(cc); out_X.append(X)
    return np.concatenate(out_k), np.concatenate(out_c), np.concatenate(out_X)


def outline_points(V, F):
    """3D-punktet som danner modellens omriss i hver kolonne (bottom) og rad
    (front), for aa vite hvilke x, y, z bildet maaler. Returnerer (Xb, Xf)."""
    Fk = _faces(V, F)
    k, cc, X = _crossings(CAM, V, Fk, BOT[:, 0], "col")
    Xb = np.full((len(BOT), 3), np.nan)
    for i in range(len(BOT)):
        m = k == i
        if m.any():
            Xb[i] = X[m][np.argmax(cc[m])]
    k, cc, X = _crossings(CAM, V, Fk, FRONT[:, 0], "row")
    Xf = np.full((len(FRONT), 3), np.nan)
    for i in range(len(FRONT)):
        m = k == i
        if m.any():
            Xf[i] = X[m][np.argmax(cc[m])]
    return Xb, Xf


def mm_per_px(X):
    """Omtrentlig mm per px ved 3D-punktene X (avstand langs kameraaksen / f)."""
    Q = (np.asarray(X, float) - CAM.C) @ CAM.R.T
    return Q[:, 2] / CAM.f


# ---------------------------------------------------------------- stripen forut
def _zline(V, F, zf, xmax=4600.0):
    """Skjaering mellom nettet og flaten z = zf(x) (eller konstant zf) paa
    styrbord side (y > 5)."""
    zfun = zf if callable(zf) else (lambda x, z0=float(zf): np.full(np.shape(x), z0))
    E = np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]
    E = np.unique(np.sort(E, axis=1), axis=0)
    A, B = V[E[:, 0]], V[E[:, 1]]
    ha, hb = A[:, 2] - zfun(A[:, 0]), B[:, 2] - zfun(B[:, 0])
    m = (ha * hb < 0) & (np.minimum(A[:, 0], B[:, 0]) < xmax + 300.0) & (np.maximum(A[:, 1], B[:, 1]) > 5.0)
    t = ha[m] / (ha[m] - hb[m])
    return A[m] + t[:, None] * (B[m] - A[m])


def _line_resid(V, F, zf, obs, xmax):
    X = _zline(V, F, zf, xmax)
    if len(X) < 3:
        return np.full(len(obs), CAP)
    u, v, d = CAM.project(X)
    sel = X[:, 0] <= xmax
    uu, vv = u[sel], v[sel]
    o = np.argsort(uu)
    uu, vv = uu[o], vv[o]
    inside = (obs[:, 0] >= uu[0]) & (obs[:, 0] <= uu[-1])
    return np.where(inside, np.interp(obs[:, 0], uu, vv) - obs[:, 1], CAP)


def resid_bt(V, F, z0=None, xmax=4600.0):
    """Stripens nedre kant forut (x < xmax): modell_v - obs_v (positivt =
    modellens linje lavere i bildet enn fotoets) for linja
    z = 38 + bt_dz_red + k (x - 4000)/1000 paa styrbord side. Kolonner utenfor
    den synlige delen av linja faar CAP."""
    zf = (lambda x: 38.0 + DZR + KBT * (np.asarray(x) - 4000.0) / 1000.0) if z0 is None else z0
    return _line_resid(V, F, zf, BTR, xmax)


def resid_bt_top(V, F, xmax=4600.0):
    """Kontroll: stripens blaa overkant forut, z = bt_top_z(x) + bt_dz_top
    (IMG_9370: 146 ved x 1 000 -> 125 fra x 5 500)."""
    zf = lambda x: (146.0 + (125.0 - 146.0) * np.clip((np.asarray(x) - 1000.0) / 4500.0, 0.0, 1.0) + DZT
                    + KBT * (np.asarray(x) - 4000.0) / 1000.0)
    return _line_resid(V, F, zf, BTT, xmax)


# ---------------------------------------------------------------- oppsummering
_DIAG = {}


def _diag(V, F):
    """x for hver kolonne/rad og mm/px, regnet en gang (paa foerste nett)."""
    if "xb" not in _DIAG:
        Xb, Xf = outline_points(V, F)
        _DIAG.update(xb=Xb, xf=Xf, mmb=mm_per_px(Xb), mmf=mm_per_px(Xf))
    return _DIAG


def summary(V, F, tag=""):
    t0 = time.time()
    rb, rf = parts(V, F)
    dt = time.time() - t0
    D = _diag(V, F)
    xb, xf = D["xb"][:, 0], D["xf"][:, 0]
    regs = [("front: forfot (rad 352-440)", rf, D["mmf"], np.ones(len(rf), bool))]
    for a, b in ((0, 1500), (1500, 2000), (2000, 2500), (2500, 3000), (3000, 9000)):
        regs.append(("bunn x %4d-%4d" % (a, min(b, 3300)), rb, D["mmb"], (xb >= a) & (xb < b)))
    lines = []
    for name, r, mmpx, m in regs:
        if not m.any():
            continue
        rr, mm = r[m], (r * mmpx)[m]
        lines.append("  %-30s n %3d  middel %+6.1f px (%+5.0f mm)  rms %5.1f px (%4.0f mm)  maks %+6.1f px"
                     % (name, m.sum(), rr.mean(), mm.mean(), np.sqrt(np.mean(rr ** 2)), np.sqrt(np.mean(mm ** 2)),
                        rr[np.argmax(np.abs(rr))]))
    rbt = resid_bt(V, F)
    ok = rbt != CAP
    lines.append("  %-30s n %3d  middel %+6.1f px  rms %5.1f px (kontroll av kamera/stripehoeyde)"
                 % ("stripens nedre kant x<4600", ok.sum(), rbt[ok].mean() if ok.any() else np.nan,
                    np.sqrt(np.mean(rbt[ok] ** 2)) if ok.any() else np.nan))
    allr = np.r_[rb, rf]
    print("IMG_9389 forkropp %s: alle n %d middel %+.1f rms %.1f px (+ = modellen utenfor bildets omriss)  [%.3f s]"
          % (tag, len(allr), allr.mean(), np.sqrt(np.mean(allr ** 2)), dt))
    print("\n".join(lines), flush=True)
    return dict(bottom=rb, front=rf, bt=rbt, x_bottom=xb, x_front=xf)


if __name__ == "__main__":
    import photos
    V, F = photos.mesh()
    t0 = time.time()
    r = resid(V, F)
    t1 = time.time()
    print("resid: %d rester, %.3f s; kolonner tatt ut for kjolen: %d" % (len(r), t1 - t0, (~_KOK).sum()))
    s = summary(V, F, "dagens modell")
    D = _diag(V, F)
    print("omrisset (bunn): x %.0f-%.0f, y %.0f-%.0f, z %.0f..%.0f"
          % (np.nanmin(D["xb"][:, 0]), np.nanmax(D["xb"][:, 0]), np.nanmin(D["xb"][:, 1]), np.nanmax(D["xb"][:, 1]),
             np.nanmin(D["xb"][:, 2]), np.nanmax(D["xb"][:, 2])))
    print("omrisset (front): x %.0f-%.0f, y %.0f-%.0f, z %.0f..%.0f"
          % (np.nanmin(D["xf"][:, 0]), np.nanmax(D["xf"][:, 0]), np.nanmin(D["xf"][:, 1]), np.nanmax(D["xf"][:, 1]),
             np.nanmin(D["xf"][:, 2]), np.nanmax(D["xf"][:, 2])))
