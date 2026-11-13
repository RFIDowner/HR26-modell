"""Analytic hull mesh from curves.section (no CAD), pinhole camera, silhouette extents, hydrostatics."""
import math, sys
sys.path.insert(0, '.')
import numpy as np
import common as c


def look_rot(fwd, up=(0, 0, 1)):
    f = np.asarray(fwd, float); f = f / np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r)
    d = np.cross(f, r)
    return np.array([r, d, f])


def rot_from_euler(yaw, pitch, roll=0.0):
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    R = look_rot(np.array([cy * cp, sy * cp, -sp]))
    if roll:
        a = math.radians(roll)
        r, d = R[0].copy(), R[1].copy()
        R = np.array([math.cos(a) * r + math.sin(a) * d, -math.sin(a) * r + math.cos(a) * d, R[2]])
    return R


class Cam:
    def __init__(self, p, W, H):
        self.p = np.asarray(p, float)
        self.C = self.p[:3]; self.R = rot_from_euler(*self.p[3:6]); self.f = self.p[6]
        self.W, self.H = W, H; self.cx, self.cy = W / 2.0, H / 2.0

    def project(self, X):
        Q = (np.asarray(X, float) - self.C) @ self.R.T
        z = np.maximum(Q[:, 2], 1e-6)
        return self.f * Q[:, 0] / z + self.cx, self.f * Q[:, 1] / z + self.cy, Q[:, 2]


def transom_x(z, y):
    P = c.P
    R = P.TRANSOM_CAMBER_R
    sag = R - np.sqrt(np.maximum(R * R - y * y, 0.0))
    return P.TRANSOM_WL_X + P.TRANSOM_RAKE * z - sag * math.sqrt(1.0 + P.TRANSOM_RAKE ** 2)


def station_list(n=240, x1=None):
    P = c.P
    x1 = P.LOA + 20.0 if x1 is None else x1
    t = np.linspace(0.0, 1.0, n)
    s = 0.5 * (0.5 * (1 - np.cos(np.pi * t))) + 0.5 * t
    return 2.0 + (x1 - 2.0) * s


def hull_rings(xs, nsec=60, ndeck=10, zmin=None):
    C = c.C
    rings = []
    for x in xs:
        sec = np.asarray(C.section(float(x), nsec), float)
        arc = np.asarray(C.deck_arc(float(x), ndeck), float)
        prt = sec[::-1].copy(); prt[:, 0] *= -1.0
        ring = np.vstack([sec, arc[1:-1], prt[:-1]])
        rings.append(np.c_[np.full(len(ring), float(x)), ring])
    R = np.array(rings)
    xt = transom_x(R[..., 2], R[..., 1])
    R[..., 0] = np.minimum(R[..., 0], xt)
    return R


def rings_to_mesh(R):
    ns, nr, _ = R.shape
    V = R.reshape(-1, 3)
    idx = np.arange(ns * nr).reshape(ns, nr)
    a = idx[:-1, :]; b = np.roll(idx[:-1, :], -1, axis=1)
    cc = idx[1:, :]; d = np.roll(idx[1:, :], -1, axis=1)
    F = np.r_[np.c_[a.ravel(), b.ravel(), d.ravel()], np.c_[a.ravel(), d.ravel(), cc.ravel()]]
    return V, F


def hull_mesh(n_st=240, nsec=60):
    return rings_to_mesh(hull_rings(station_list(n_st), nsec))


def row_extents(cam, V, F, rows, axis="row", zmin=150.0):
    """Exact min/max of the projected mesh per image row (or column).

    13.11.2026 kveld: rows maa vaere jevnt fordelt (r0 og dr leses fra foerste
    og siste). Har de hull, regnes det paa et jevnt rutenett og leses av
    (maaleagenten for IMG_9374 fant at e9387/e9395 ellers ble skjeve)."""
    rows = np.asarray(rows, float)
    if len(rows) > 2:
        d = np.diff(rows)
        if np.ptp(d) > 1e-6 * max(1.0, float(np.abs(d).max())):
            nz = np.abs(d[np.abs(d) > 1e-9])
            step = max(0.5, float(nz.min())) if len(nz) else 1.0
            a, b = float(np.floor(rows.min())), float(np.ceil(rows.max()))
            grid = np.arange(a, b + 0.5 * step, step)
            lo_g, hi_g = row_extents(cam, V, F, grid, axis, zmin)
            def itp(y, fill):
                ok = np.isfinite(y)
                if ok.sum() < 2:
                    return np.full(len(rows), fill)
                out = np.interp(rows, grid[ok], y[ok], left=np.nan, right=np.nan)
                # rader der rutenettet ikke traff nettet, beholdes som ikke-treff
                k = np.clip(np.round((rows - a) / step).astype(int), 0, len(grid) - 1)
                out = np.where(np.isfinite(y[k]) | np.isfinite(out), out, np.nan)
                return np.where(np.isfinite(out), out, fill)
            return itp(lo_g, np.inf), itp(hi_g, -np.inf)
    u, v, z = cam.project(V)
    if axis == "col":
        u, v = v, u
    ok = (z[F] > zmin).all(1)
    Fk = F[ok]
    U, Wv = u[Fk], v[Fk]
    rows = np.asarray(rows, float)
    lo = np.full(len(rows), np.inf); hi = np.full(len(rows), -np.inf)
    if len(rows) == 0:
        return lo, hi
    r0, dr = rows[0], (rows[-1] - rows[0]) / max(len(rows) - 1, 1)
    for e0, e1 in ((0, 1), (1, 2), (2, 0)):
        wa, wb = Wv[:, e0], Wv[:, e1]; ua, ub = U[:, e0], U[:, e1]
        wl, wh = np.minimum(wa, wb), np.maximum(wa, wb)
        k0 = np.clip(np.ceil((wl - r0) / dr).astype(np.int64), 0, len(rows))
        k1 = np.clip(np.floor((wh - r0) / dr).astype(np.int64), -1, len(rows) - 1)
        n = np.maximum(k1 - k0 + 1, 0); tot = int(n.sum())
        if tot == 0:
            continue
        eid = np.repeat(np.arange(len(n)), n)
        off = np.arange(tot) - np.repeat(np.cumsum(n) - n, n)
        kk = k0[eid] + off
        rv = r0 + kk * dr
        den = wb[eid] - wa[eid]
        t = np.where(np.abs(den) > 1e-12, (rv - wa[eid]) / np.where(np.abs(den) > 1e-12, den, 1.0), 0.0)
        uu = ua[eid] + t * (ub[eid] - ua[eid])
        np.minimum.at(lo, kk, uu); np.maximum.at(hi, kk, uu)
    return lo, hi


def hydro(n=160):
    """Canoe body below z=0: volume m3, LWL (stem crossing -> transom crossing), max WL beam, waterplane m2."""
    C, P = c.C, c.P
    xs_all = np.linspace(500.0, P.LOA, 2000)
    bz = np.array([C.bottom_z(x) for x in xs_all])
    i0 = np.argmax(bz < 0)
    x_fwd = float(np.interp(0.0, [bz[i0], bz[i0 - 1]], [xs_all[i0], xs_all[i0 - 1]]))
    x_aft = float(transom_x(0.0, 0.0))
    xs = np.linspace(x_fwd, x_aft, n)
    area, wl = [], []
    for x in xs:
        p = C._section_geom(float(x))["pts"]
        if p[0, 1] >= -0.5:
            area.append(0.0); wl.append(0.0); continue
        zz = np.linspace(p[0, 1], 0.0, 120)
        yy = np.interp(zz, p[:, 1], p[:, 0])
        # transom: only the part forward of the transom surface counts (approx: section x < transom_x(z,y))
        area.append(2.0 * float(np.trapezoid(yy, zz)))
        wl.append(float(np.interp(0.0, p[:, 1], p[:, 0])))
    area = np.array(area); wl = np.array(wl)
    vol = float(np.trapezoid(area, xs)) / 1e9
    awp = float(np.trapezoid(2 * wl, xs)) / 1e6
    lcb = float(np.trapezoid(area * xs, xs) / np.trapezoid(area, xs))
    return dict(vol=vol, lwl=x_aft - x_fwd, x_fwd=x_fwd, x_aft=x_aft, bwl=2 * wl.max(), x_bwl=float(xs[np.argmax(wl)]),
                awp=awp, lcb=lcb, amax=float(area.max()) / 1e6, x_amax=float(xs[np.argmax(area)]))
