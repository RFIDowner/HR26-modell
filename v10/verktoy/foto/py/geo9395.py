"""Modellgeometri for IMG_9395-arbeidet (ingen CAD-solider bygges).

  hull_line(zfun, xs, side=-1)  3D-linje paa skrogflaten i hoeyden zfun(x) (babord: side -1)
  keel_mesh(), rudder_mesh()    enkle trekantnett av kjolen og roret (NACA-snitt som i appendages)
  centreline()                  senterlinjen (kjol/stevn) y = 0, z = bottom_z(x)
  poly_dist(obs, uv)            avstand fra punkter til en polylinje i bildet
"""
import math

import numpy as np

import common as c

P, C = c.P, c.C
ZT_X, ZT_Z = (1000.0, 5500.0), (146.0, 125.0)       # stripens overkant (IMG_9370)
Z_RED = 38.0                                        # overgang til roedt (IMG_9370)

_SEC = {}


def section(x, n=160):
    k = (round(float(x), 3), n)
    s = _SEC.get(k)
    if s is None:
        s = np.asarray(C.section(float(x), n), float)
        _SEC[k] = s
    return s


def y_at(x, z, n=160):
    """Halv bredde paa skrogflaten ved (x, z), eller nan utenfor spantet."""
    s = section(x, n)
    if z < s[0, 1] or z > s[-1, 1]:
        return np.nan
    zz = s[:, 1]
    # sidekurven er monoton i z fra kjolen til dekkskanten
    i = int(np.searchsorted(zz, z))
    i = min(max(i, 1), len(zz) - 1)
    t = (z - zz[i - 1]) / max(zz[i] - zz[i - 1], 1e-9)
    return float(s[i - 1, 0] + t * (s[i, 0] - s[i - 1, 0]))


def z_top(x):
    return float(np.interp(x, ZT_X, ZT_Z))


def hull_line(zfun, xs, side=-1.0, dy=0.0):
    pts = []
    for x in xs:
        z = float(zfun(x))
        y = y_at(x, z)
        if not np.isfinite(y):
            continue
        xt = c.C.transom_x(z, y) if hasattr(c.C, "transom_x") else 1e9
        if x > xt:
            continue
        pts.append((x, side * (y + dy), z))
    return np.array(pts, float)


def centreline(xs):
    return np.c_[xs, np.zeros(len(xs)), [C.bottom_z(float(x)) for x in xs]]


def _foil(chord, thick, n=16):
    t = thick / chord
    beta = np.pi * np.arange(n + 1) / n
    xc = 0.5 * (1.0 - np.cos(beta))
    yt = 5.0 * t * (0.2969 * np.sqrt(xc) - 0.1260 * xc - 0.3516 * xc ** 2 + 0.2843 * xc ** 3 - 0.1015 * xc ** 4)
    up = np.c_[xc * chord, yt * chord]
    lo = np.c_[xc * chord, -yt * chord][::-1][1:-1]
    return np.r_[up, lo]


def _loft(rings):
    R = np.asarray(rings)
    ns, nr, _ = R.shape
    V = R.reshape(-1, 3)
    idx = np.arange(ns * nr).reshape(ns, nr)
    a = idx[:-1, :]; b = np.roll(idx[:-1, :], -1, axis=1)
    cc = idx[1:, :]; d = np.roll(idx[1:, :], -1, axis=1)
    F = np.r_[np.c_[a.ravel(), b.ravel(), d.ravel()], np.c_[a.ravel(), d.ravel(), cc.ravel()]]
    # lokk i enden (vifte fra foerste punkt)
    last = idx[-1]
    F = np.r_[F, np.c_[np.full(nr - 2, last[0]), last[1:-1], last[2:]]]
    return V, F


def keel_mesh(nz=48, nf=16, z_top=-330.0):
    from hr26 import appendages as A
    k = A._KeelProfile()
    zs = np.r_[np.linspace(z_top, k.zb + 60.0, nz - 6), np.linspace(k.zb + 50.0, k.zb, 6)]
    rings = []
    for z in zs:
        le, te = k.edges(float(z))
        th = P.KEEL_ROOT_T
        e = z - k.zb
        if e < P.KEEL_BOT_CHAMFER:
            th -= 2.0 * (P.KEEL_BOT_CHAMFER - e)
        f = _foil(max(te - le, 50.0), max(th, 20.0), nf)
        rings.append(np.c_[le + f[:, 0], f[:, 1], np.full(len(f), z)])
    return _loft(rings)


def rudder_mesh(n=12, nf=14):
    rings = []
    for i in range(n + 1):
        t = i / n
        z = P.RUDDER_TOP_Z + (P.RUDDER_BOT_Z - P.RUDDER_TOP_Z) * t
        le = P.RUDDER_X + P.RUDDER_RAKE * t
        ch = P.RUDDER_TE_X - le
        th = P.RUDDER_T * (1.0 - 0.28 * t)
        f = _foil(ch, th, nf)
        rings.append(np.c_[le + f[:, 0], f[:, 1], np.full(len(f), z)])
    return _loft(rings)


def poly_dist(obs, uv):
    """Avstand fra hvert observert punkt (N,2) til polylinjen uv (M,2)."""
    a = uv[:-1][None, :, :]; b = uv[1:][None, :, :]
    p = obs[:, None, :]
    ab = b - a
    t = np.clip(((p - a) * ab).sum(-1) / np.maximum((ab * ab).sum(-1), 1e-9), 0.0, 1.0)
    q = a + t[..., None] * ab
    return np.sqrt(((p - q) ** 2).sum(-1)).min(1)


def poly_signed(obs, uv, nrm_sign=1.0):
    """Fortegnsavstand: positiv naar punktet ligger til venstre for polylinjen (i
    bildekoordinater, v nedover) ganger nrm_sign."""
    a = uv[:-1][None, :, :]; b = uv[1:][None, :, :]
    p = obs[:, None, :]
    ab = b - a
    t = np.clip(((p - a) * ab).sum(-1) / np.maximum((ab * ab).sum(-1), 1e-9), 0.0, 1.0)
    q = a + t[..., None] * ab
    d = np.sqrt(((p - q) ** 2).sum(-1))
    j = d.argmin(1)
    i = np.arange(len(obs))
    cr = ab[0, j, 0] * (p[i, 0, 1] - a[0, j, 1]) - ab[0, j, 1] * (p[i, 0, 0] - a[0, j, 0])
    return np.sign(cr) * d[i, j] * nrm_sign
