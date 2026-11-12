"""Shared helpers for the underwater-body study (undervann).

Everything is in the build frame, full-scale mm: x from the bow aft, y to
starboard, z up from the DWL.  The hull model is imported from the snapshot
copy in ../snap (never from the repo), and score.py is loaded from the copy in
../snap/score.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys

import numpy as np

ROOT = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/undervann"
SNAP = ROOT + "/snap"
OUT = ROOT
PHOTOS = r"C:/Users/stig/Documents/Seilbåt"
STL4 = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/v10run/int4_0.02_0.15.stl"

if SNAP not in sys.path:
    sys.path.insert(0, SNAP)
from hr26 import curves as C          # noqa: E402
from hr26 import params as P          # noqa: E402


def _load_score():
    spec = importlib.util.spec_from_file_location("score_snap", SNAP + "/score/score.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


S = _load_score()
PV = {v["file"][:8]: v for v in S.PHOTO_VIEWS}


# ------------------------------------------------------------------ photos
def photo(name):
    """Upright (EXIF-rotated) photo as an RGB uint8 array."""
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(f"{PHOTOS}/{name}.jpeg")).convert("RGB")
    return np.asarray(im)


PHOTO_WH = {"IMG_9388": (1500, 2000), "IMG_9391": (1500, 2000), "IMG_9389": (2000, 1500)}


def cam_from(p, name):
    """Camera from (x, y, z, yaw, pitch, roll, f) for the full-size upright photo."""
    W, H = PHOTO_WH[name]
    return S.Cam(np.array(p[:3], float), S.rot_from_euler(p[3], p[4], p[5]), W, H, f=p[6],
                 cx=W / 2.0, cy=H / 2.0)


def cam_params0(name):
    v = PV[name]
    return [*v["C"], v["yaw"], v["pitch"], v["roll"], v["f"]]


# --------------------------------------------------------------- STL (int4)
def load_int4():
    T, _ = S.load_stl(STL4)
    V, F = S.weld(T, 1e-5)
    V = V.copy()
    V[:, 0] = V[:, 0] * 30.0 + 4.0
    V[:, 1] = V[:, 1] * 30.0
    V[:, 2] = V[:, 2] * 30.0 - 1400.0
    return V, F


# ------------------------------------------------------- analytic hull mesh
def station_list(n=260, x0=0.0, x1=None):
    """Stations, denser at both ends (cosine) plus a uniform share."""
    x1 = P.LOA + 20.0 if x1 is None else x1
    t = np.linspace(0.0, 1.0, n)
    s = 0.5 * (0.5 * (1 - np.cos(np.pi * t))) + 0.5 * t
    return x0 + (x1 - x0) * s


def hull_rings(xs, nsec=60, ndeck=10, section_fn=None):
    """One closed ring per station: starboard side keel->deck edge, deck arc,
    port side deck edge->keel.  Returns array (nst, nring, 3), transom-clamped."""
    sec_fn = section_fn or (lambda x, n: C.section(x, n))
    rings = []
    for x in xs:
        sec = np.asarray(sec_fn(float(x), nsec), float)            # (nsec, 2): keel -> D
        arc = np.asarray(C.deck_arc(float(x), ndeck), float)       # +bd ... -bd
        stb = sec
        prt = sec[::-1].copy()
        prt[:, 0] *= -1.0
        ring = np.vstack([stb, arc[1:-1], prt[:-1]])              # port keel point = stb keel (dropped)
        X = np.full(len(ring), float(x))
        rings.append(np.c_[X, ring[:, 0], ring[:, 1]])
    R = np.array(rings)
    # clamp everything aft of the transom surface onto it
    y, z = R[..., 1], R[..., 2]
    Rt = P.TRANSOM_CAMBER_R
    sag = Rt - np.sqrt(np.maximum(Rt * Rt - y * y, 0.0))
    xt = P.TRANSOM_WL_X + P.TRANSOM_RAKE * z - sag * math.sqrt(1.0 + P.TRANSOM_RAKE ** 2)
    R[..., 0] = np.minimum(R[..., 0], xt)
    return R


def rings_to_mesh(R):
    ns, nr, _ = R.shape
    V = R.reshape(-1, 3)
    idx = np.arange(ns * nr).reshape(ns, nr)
    a = idx[:-1, :]
    b = np.roll(idx[:-1, :], -1, axis=1)
    c = idx[1:, :]
    d = np.roll(idx[1:, :], -1, axis=1)
    F = np.r_[np.c_[a.ravel(), b.ravel(), d.ravel()], np.c_[a.ravel(), d.ravel(), c.ravel()]]
    return V, F


def hull_mesh(n_st=260, nsec=60, ndeck=10, section_fn=None, xs=None):
    xs = station_list(n_st) if xs is None else xs
    return rings_to_mesh(hull_rings(xs, nsec, ndeck, section_fn))


# --------------------------------------------- silhouette extents of a mesh
def row_extents(cam, V, F, rows, axis="row", zmin=150.0):
    """Exact min/max of the projected mesh along each image row (axis='row':
    returns umin, umax per v in rows) or column (axis='col': vmin, vmax per u).
    Triangles with a vertex closer than zmin to the camera plane are dropped.
    Returns (lo, hi, dlo, dhi) where d* is the camera depth of the extreme."""
    u, v, z = cam.project(V)
    if axis == "col":
        u, v = v, u
    ok = (z[F] > zmin).all(1)
    Fk = F[ok]
    U, W, Z = u[Fk], v[Fk], z[Fk]
    rows = np.asarray(rows, float)
    lo = np.full(len(rows), np.inf)
    hi = np.full(len(rows), -np.inf)
    dlo = np.full(len(rows), np.nan)
    dhi = np.full(len(rows), np.nan)
    if len(rows) == 0:
        return lo, hi, dlo, dhi
    r0, dr = rows[0], (rows[-1] - rows[0]) / max(len(rows) - 1, 1)
    for e0, e1 in ((0, 1), (1, 2), (2, 0)):
        wa, wb = W[:, e0], W[:, e1]
        ua, ub = U[:, e0], U[:, e1]
        za, zb = Z[:, e0], Z[:, e1]
        wl, wh = np.minimum(wa, wb), np.maximum(wa, wb)
        k0 = np.ceil((wl - r0) / dr).astype(np.int64)
        k1 = np.floor((wh - r0) / dr).astype(np.int64)
        k0 = np.clip(k0, 0, len(rows))
        k1 = np.clip(k1, -1, len(rows) - 1)
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
        uu = ua[eid] + t * (ub[eid] - ua[eid])
        zz = za[eid] + t * (zb[eid] - za[eid])
        # min / max per row with the depth of the winner
        o = np.lexsort((uu, kk))
        ks, us, zs = kk[o], uu[o], zz[o]
        first = np.r_[True, ks[1:] != ks[:-1]]
        last = np.r_[ks[1:] != ks[:-1], True]
        m = us[first] < lo[ks[first]]
        lo[ks[first][m]] = us[first][m]
        dlo[ks[first][m]] = zs[first][m]
        m = us[last] > hi[ks[last]]
        hi[ks[last][m]] = us[last][m]
        dhi[ks[last][m]] = zs[last][m]
    return lo, hi, dlo, dhi


def save_json(obj, path):
    def conv(o):
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        raise TypeError(type(o))
    with open(path, "w") as fh:
        json.dump(obj, fh, default=conv, indent=1)
