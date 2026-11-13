"""Forkroppen i IMG_9395 som residualer for tilpasningen (trinn 5).

Kameraet ser forfra-nedenfra fra babord (nesten rett forfra, 12 grader opp): i bildet er u nesten -y
(styrbord til venstre, ca. 2,6 px per 10 mm) og v nesten -z (ca. 2,2-2,4 px per 10 mm). Omrisset av
forkroppen dannes av STYRBORD side: radene (venstre kant) maaler styrbord halvbredde, kolonnene (nedre
kant) maaler dybden av styrbord bunn/slag.

  CAM                 kameraet (uwlib.Cam), loest i cam9395.py UTEN forkroppen og uten stripen
  resid(V, F)         1-D array, fortegnet px, positiv = modellen ligger UTENFOR bildets omriss
                      (rader: modellen lenger til venstre = bredere; kolonner: modellen lavere = dypere).
                      Rekkefolge: ROWS (rad 705-945, forfot og styrbord bunn, x ca. 900-2800), saa COLS
                      (kolonne 1121-1299, bunnen x ca. 2650-3700). n = len(WEIGHTS).
  WEIGHTS             vekt per element i resid: 0.5 der loftestroppen ligger langs omrisset (u < 1180,
                      rad > 900; omrisset kan vaere 3-6 px for langt ute), ellers 1.
  resid_keelroot(V,F) kolonne 1300-1335 (de siste ca. 40 px foran kjolens forkant, x ca. 3850-4000):
                      holdt utenfor resid fordi en hulkil ved kjolroten paa baaten kan danne omrisset der.
  resid_bow(V, F)     venstre omriss rad 545-705 (baugen OVER vann, z ca. 300-650, x ca. 700-950).
  resid_bt(V, F)      stripens nedre kant (babord) mot modellens linje z = BT_Z (snitt av nettet med
                      planet z = BT_Z, y < 0), px, positiv = modellens linje LAVERE i bildet. Merk: i
                      denne vinkelen maaler linja nesten bare hoeyden (2,3 px per 10 mm), ikke bredden
                      (ca. 0,2 px per 10 mm), saa den er svak for formen.
  resid_keelline(V,F) modellens kjollinje (laveste punkt i y = 0) mot grensen roedt/graatt paa forfoten,
                      per rad, px, positiv = modellens kjollinje til venstre for grensen. Tolkning:
                      grensen er trolig kjollinjen (V-en), se summary.
  summary(V, F)       skriver snitt/rms per omraade (med x, z, |y| for punktene som danner omrisset og
                      omtrent mm) og returnerer en dict.

(V, F) er et hvilket som helst trekantnett av skroget i baatens ramme (mm, x fra stevnen, y styrbord +,
z fra DWL), f.eks. photos.mesh() = uwlib.hull_mesh(220, 60), eller uwlib.hull_mesh(...) etter
common.reload_model(...). resid tar ca. 20 ms.
"""
import json

import numpy as np

import common as c
import uwlib as U

_J = json.load(open(c.W + "/out/t9395_forkropp.json"))
_CJ = json.load(open(c.W + "/out/cam9395.json"))
CAM = U.Cam(_CJ["p"], _CJ["W"], _CJ["H"])
BT_Z = float(_J["bt_z"])

_R = np.asarray(_J["outline_rows"], float)
_RK = np.asarray(_J["outline_rows_keep"], bool)
ROWS = _R[_RK]                                   # [v, u]
_C = np.asarray(_J["outline_cols"], float)
_CK = np.asarray(_J["outline_cols_keep"], bool)
COLS_ALL = _C[_CK]                               # [u, v]
COLS = COLS_ALL[COLS_ALL[:, 0] < 1300]
COLS_KR = COLS_ALL[COLS_ALL[:, 0] >= 1300]
BOW = np.asarray(_J["bow_left_above_wl"], float)  # [v, u]
BT = np.asarray(_J["bt_lower"], float)           # [u, v]
BT = BT[BT[:, 0] >= 1047]
RG_ROWS = np.asarray(_J["red_grey_rows"], float)  # [v, u]
STRAP = tuple(_J["strap_cols"])
WEIGHTS = np.r_[np.where(ROWS[:, 0] > 900, 0.5, 1.0), np.where(COLS[:, 0] < 1180, 0.5, 1.0)]

# omraader for summary
REG_ROWS = {"forfot rad 705-850": (705, 850), "styrbord bunn rad 850-945": (850, 946)}
REG_COLS = {"bunn u 1121-1180 (stropp)": (1121, 1180), "bunn u 1180-1215": (1180, 1216),
            "bunn foran kjolen u 1252-1299": (1252, 1300)}


def _lo_rows(V, F, rows):
    lo, _ = U.row_extents(CAM, V, F, rows)
    return lo


def resid(V, F):
    lo = _lo_rows(V, F, ROWS[:, 0])
    rr = np.where(np.isfinite(lo), ROWS[:, 1] - lo, -40.0)
    _, hi = U.row_extents(CAM, V, F, COLS[:, 0], axis="col")
    rc = np.where(np.isfinite(hi), hi - COLS[:, 1], -40.0)
    return np.r_[rr, rc]


def resid_keelroot(V, F):
    _, hi = U.row_extents(CAM, V, F, COLS_KR[:, 0], axis="col")
    return np.where(np.isfinite(hi), hi - COLS_KR[:, 1], -40.0)


def keelline(V, F, xmin=600.0, xmax=3400.0, nb=200):
    """Laveste punkt i planet y = 0 per x-bin (kjollinjen/stevnen) fra nettet."""
    P3 = V[F]
    s = P3[:, :, 1]
    out = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        a, b = s[:, i], s[:, j]
        m = (a * b < 0) | ((a == 0) & (b != 0))
        den = np.where(a[m] - b[m] == 0, 1.0, a[m] - b[m])
        t = a[m] / den
        out.append(P3[m, i] + t[:, None] * (P3[m, j] - P3[m, i]))
    # punkter som ligger i y = 0
    on = V[np.abs(V[:, 1]) < 1e-6]
    p = np.vstack(out + [on])
    p = p[(p[:, 0] >= xmin) & (p[:, 0] <= xmax)]
    edges = np.linspace(xmin, xmax, nb + 1)
    k = np.digitize(p[:, 0], edges) - 1
    res = []
    for q in range(nb):
        g = p[k == q]
        if len(g):
            res.append(g[np.argmin(g[:, 2])])
    return np.array(res)


def resid_keelline(V, F):
    X = keelline(V, F)
    u, v, _ = CAM.project(X)
    o = np.argsort(v)
    um = np.interp(RG_ROWS[:, 0], v[o], u[o], left=np.nan, right=np.nan)
    return np.where(np.isfinite(um), RG_ROWS[:, 1] - um, 40.0)


def resid_bow(V, F):
    lo = _lo_rows(V, F, BOW[:, 0])
    return np.where(np.isfinite(lo), BOW[:, 1] - lo, -40.0)


def zline(V, F, z0, port=True, xmin=700.0, xmax=5200.0):
    """Punkter der nettet krysser planet z = z0 (babord, y < 0), sortert etter x."""
    P3 = V[F]                                     # (nf, 3, 3)
    s = P3[:, :, 2] - z0
    out = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        a, b = s[:, i], s[:, j]
        m = (a * b < 0)
        t = a[m] / (a[m] - b[m])
        p = P3[m, i] + t[:, None] * (P3[m, j] - P3[m, i])
        out.append(p)
    p = np.vstack(out)
    k = (p[:, 1] < 0) if port else (p[:, 1] > 0)
    k &= (p[:, 0] >= xmin) & (p[:, 0] <= xmax)
    p = p[k]
    if len(p) == 0:
        return p
    # en side: behold det ytterste punktet per x (nettet kan krysse planet ogsaa ved kjolen)
    o = np.argsort(p[:, 0])
    p = p[o]
    xr = np.round(p[:, 0], 1)
    _, first = np.unique(xr, return_index=True)
    best = []
    for g in np.split(np.arange(len(p)), first[1:]):
        best.append(g[np.argmin(p[g, 1])])
    return p[best]


def resid_bt(V, F, z0=None):
    z0 = BT_Z if z0 is None else z0
    X = zline(V, F, z0)
    if len(X) < 3:
        return np.full(len(BT), 40.0)
    u, v, _ = CAM.project(X)
    o = np.argsort(u)
    uu, vv = u[o], v[o]
    inside = (BT[:, 0] >= uu[0]) & (BT[:, 0] <= uu[-1])
    pv = np.interp(BT[:, 0], uu, vv)
    return np.where(inside, pv - BT[:, 1], 40.0)


def _gen_points(V, F, rows=None, cols=None):
    """3D-punktet paa nettet som danner modellens omriss i hver rad (min u) eller kolonne (max v):
    samme kantkryssing som uwlib.row_extents, men med punktet i rommet."""
    u, v, z = CAM.project(V)
    axis_rows = rows is not None
    lines = np.asarray(rows if axis_rows else cols, float)
    a_, b_ = (u, v) if axis_rows else (v, u)          # a: langs linja (maales), b: linjens koordinat
    ok = (z[F] > 150.0).all(1)
    Fk = F[ok]
    out = np.full((len(lines), 3), np.nan)
    best = np.full(len(lines), np.inf if axis_rows else -np.inf)
    r0, dr = lines[0], (lines[-1] - lines[0]) / max(len(lines) - 1, 1)
    for e0, e1 in ((0, 1), (1, 2), (2, 0)):
        ia, ib = Fk[:, e0], Fk[:, e1]
        wa, wb = b_[ia], b_[ib]
        wl, wh = np.minimum(wa, wb), np.maximum(wa, wb)
        k0 = np.clip(np.ceil((wl - r0) / dr).astype(np.int64), 0, len(lines))
        k1 = np.clip(np.floor((wh - r0) / dr).astype(np.int64), -1, len(lines) - 1)
        n = np.maximum(k1 - k0 + 1, 0)
        tot = int(n.sum())
        if tot == 0:
            continue
        eid = np.repeat(np.arange(len(n)), n)
        off = np.arange(tot) - np.repeat(np.cumsum(n) - n, n)
        kk = k0[eid] + off
        rv = r0 + kk * dr
        den = wb[eid] - wa[eid]
        t = np.where(np.abs(den) > 1e-12, (rv - wa[eid]) / np.where(np.abs(den) > 1e-12, den, 1.0), 0.0)
        val = a_[ia[eid]] + t * (a_[ib[eid]] - a_[ia[eid]])
        X = V[ia[eid]] + t[:, None] * (V[ib[eid]] - V[ia[eid]])
        key = val if axis_rows else -val
        o = np.lexsort((key, kk))
        kk_s, key_s = kk[o], key[o]
        first = np.r_[True, kk_s[1:] != kk_s[:-1]]
        idx = o[first]
        for j, kq in zip(idx, kk[idx]):
            better = key[j] < (best[kq] if axis_rows else -best[kq])
            if better:
                best[kq] = val[j]
                out[kq] = X[j]
    return out


def _mm_per_px(X):
    d = (X - CAM.C) @ CAM.R[2]
    return d / CAM.f


def _region(name, e, g, lines, res, note=""):
    mm = float(np.nanmedian(_mm_per_px(g))) if g is not None else np.nan
    d = dict(mean=float(np.mean(e)), rms=float(np.sqrt(np.mean(e ** 2))), n=int(len(e)), mm_per_px=mm)
    txt = f"  {name:34s} mean {d['mean']:+6.1f}  rms {d['rms']:5.1f} px"
    if g is not None and np.isfinite(g).any():
        d.update(x=(float(np.nanmin(g[:, 0])), float(np.nanmax(g[:, 0]))),
                 z=(float(np.nanmin(g[:, 2])), float(np.nanmax(g[:, 2]))),
                 y=(float(np.nanmin(np.abs(g[:, 1]))), float(np.nanmax(np.abs(g[:, 1])))))
        txt += (f"  (~{d['mean'] * mm:+5.0f} mm)  x {d['x'][0]:5.0f}-{d['x'][1]:5.0f}  z {d['z'][0]:5.0f}.."
                f"{d['z'][1]:5.0f}  |y| {d['y'][0]:4.0f}-{d['y'][1]:4.0f}")
    res[name] = d
    lines.append(txt + note)


def summary(V, F, tag="", verbose=True):
    """Snitt og rms per omraade. Fortegn som resid: + = modellen utenfor (bredere / dypere) enn bildet.
    mm = px x avstand / f ved punktet som danner modellens omriss (rader ~ halvbredde y, kolonner ~ dybde z)."""
    r = resid(V, F)
    nr = len(ROWS)
    rr, rc = r[:nr], r[nr:]
    res, lines = {}, []
    G_r = _gen_points(V, F, rows=ROWS[:, 0])
    G_c = _gen_points(V, F, cols=COLS[:, 0])
    for name, (a, b) in REG_ROWS.items():
        k = (ROWS[:, 0] >= a) & (ROWS[:, 0] < b)
        if k.any():
            _region(name, rr[k], G_r[k], lines, res)
    for name, (a, b) in REG_COLS.items():
        k = (COLS[:, 0] >= a) & (COLS[:, 0] < b)
        if k.any():
            _region(name, rc[k], G_c[k], lines, res)
    _region("kjolrot u 1300-1335 (ikke i resid)", resid_keelroot(V, F),
            _gen_points(V, F, cols=COLS_KR[:, 0]), lines, res)
    _region("baug over vann rad 545-705 (ikke i resid)", resid_bow(V, F),
            _gen_points(V, F, rows=BOW[:, 0]), lines, res)
    kl = resid_keelline(V, F)
    X = keelline(V, F)
    u, v, _ = CAM.project(X)
    o = np.argsort(v)
    xk = np.interp(RG_ROWS[:, 0], v[o], X[o, 0])
    for x0, x1 in ((800, 1500), (1500, 2500)):
        k = (xk >= x0) & (xk < x1) & (np.abs(kl) < 39)
        if k.any():
            _region(f"kjollinje mot roedt/graatt x {x0}-{x1}", kl[k], None, lines, res, "  (ikke i resid)")
    bt = resid_bt(V, F)
    X = zline(V, F, BT_Z)
    if len(X) > 3:
        u, _, _ = CAM.project(X)
        o = np.argsort(u)
        xb = np.interp(BT[:, 0], u[o], X[o, 0])
        for x0, x1 in ((800, 1500), (1500, 2500), (2500, 3500), (3500, 4600)):
            k = (xb >= x0) & (xb < x1)
            if k.any():
                _region(f"stripe z={BT_Z:.0f} x {x0}-{x1}", bt[k], None, lines, res, "  (ikke i resid)")
    w = WEIGHTS
    out = {"rows": rr, "cols": rc, "regions": res,
           "wrms": float(np.sqrt(np.sum(w * r ** 2) / np.sum(w)))}
    if verbose:
        print(f"e9395 {tag}: resid n={len(r)} mean {np.mean(r):+.1f} rms {np.sqrt(np.mean(r ** 2)):.1f} px "
              f"(vektet rms {out['wrms']:.1f})")
        print("\n".join(lines))
    return out


if __name__ == "__main__":
    import time
    import photos
    V, F = photos.mesh()
    t0 = time.time()
    for _ in range(10):
        resid(V, F)
    print("resid: %.3f s per kall, n = %d" % ((time.time() - t0) / 10, len(resid(V, F))))
    t0 = time.time()
    resid_bt(V, F)
    resid_keelline(V, F)
    print("resid_bt + resid_keelline: %.3f s" % (time.time() - t0))
    summary(V, F, "naa (photos.mesh)")
