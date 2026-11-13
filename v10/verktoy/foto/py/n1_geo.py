"""3D-trekk fra modellen (arbeidstreet, geo9374.use_model(None)) for de nye
akterbildene 13.11.2026: «nye (1)» (akterfra og nedenfra, i stroppene),
«nye (3)» (rett akterfra, paa bukker) og IMG_9526 (flytende, papirbilde).

Ingen CAD: hr26.appendages importeres med en tom stand-in for cadquery, saa
bare de rene numpy-funksjonene (_KeelProfile, _foil, keel_outline) brukes.
Modellramme: x fra baugen, y halvbredde (babord = -y), z over DWL.
"""
import sys
import types

if "cadquery" not in sys.modules:          # ingen CadQuery i denne oppgaven
    sys.modules["cadquery"] = types.ModuleType("cadquery")

import numpy as np

import common as c
import uwlib as U
import geo9374 as G

G.use_model(None)
P = c.P
C = c.C


class Cam(G.Cam9374):
    """uwlib.Cam + hovedpunkt (du, dv), radial k1/k2 og ray() for
    tilbakeprojeksjon."""

    def __init__(self, p, W, H, du=0.0, dv=0.0, k1=0.0, k2=0.0, asp=1.0):
        super().__init__(p, W, H, du=du, dv=dv, k1=k1, asp=asp)
        self.k2 = k2

    def project(self, X):
        Q = (np.asarray(X, float) - self.C) @ self.R.T
        z = np.maximum(Q[:, 2], 1e-6)
        a, b = Q[:, 0] / z, Q[:, 1] / z
        r2 = a * a + b * b
        s = 1.0 + self.k1 * r2 + self.k2 * r2 * r2
        return self.f * a * s + self.cx, self.f * self.asp * b * s + self.cy, Q[:, 2]

    def ray(self, u, v):
        ad = (np.asarray(u, float) - self.cx) / self.f
        bd = (np.asarray(v, float) - self.cy) / (self.f * self.asp)
        a, b = ad.copy(), bd.copy()
        for _ in range(40):
            r2 = a * a + b * b
            s = 1.0 + self.k1 * r2 + self.k2 * r2 * r2
            a, b = ad / s, bd / s
        d = np.stack([a, b, np.ones_like(a)], axis=-1) @ self.R
        return d / np.linalg.norm(d, axis=-1, keepdims=True)


CAMX = {"pin": [], "pp": ["du", "dv"], "k1": ["k1"], "ppk1": ["du", "dv", "k1"], "ppk12": ["du", "dv", "k1", "k2"],
        "ppasp": ["du", "dv", "asp"]}
XSX = dict(du=10.0, dv=10.0, k1=0.05, k2=0.05, asp=0.01)
LBX = dict(du=-500.0, dv=-900.0, k1=-3.0, k2=-6.0, asp=0.6)
UBX = dict(du=500.0, dv=900.0, k1=3.0, k2=6.0, asp=1.6)


def make_cam(q, mode, W, H):
    kw = dict(zip(CAMX[mode], q[7:7 + len(CAMX[mode])]))
    return Cam(q[:7], W, H, **kw)


side_y = G.side_y


def corner_y(z):
    """Akterspeilhjoernet (skrogsiden moeter akterspeilsflaten) i hoeyden z:
    (x, y) med y >= 0, eller None (der skroget er smalere enn 1 mm)."""
    x = C.transom_x(z, 0.0)
    if not np.isfinite(side_y(x, z)) or side_y(x, z) <= 1.0:
        return None
    lo, hi = 0.0, 1500.0
    for _ in range(40):
        m = 0.5 * (lo + hi)
        ys = side_y(C.transom_x(z, m), z)
        if np.isfinite(ys) and ys > m:
            lo = m
        else:
            hi = m
    y = 0.5 * (lo + hi)
    return C.transom_x(z, y), y


def corner_line(z0=-420.0, z1=None, dz=10.0, side=1.0):
    """Hjoernelinja (x, side*y, z) fra z0 til listen."""
    if z1 is None:
        z1 = strake_corner()[2]
    out = []
    for z in np.arange(z0, z1 + 0.1, dz):
        k = corner_y(float(z))
        if k is not None:
            out.append((k[0], side * k[1], float(z)))
    return np.array(out)


def strake_corner():
    """Der listen (paa siden) moeter akterspeilet: (x, y, z), y > 0."""
    xe = G.strake_end_x()
    z = C.strake_z(xe)
    return np.array([xe, side_y(xe, z), z])


def strake_side(side=-1.0, x0=4000.0, n=200):
    """Listens senter paa siden (skrog + proud/2)."""
    s = G.strake3(x0, None, n)          # babord (-y)
    s[:, 1] *= -side
    return s


def strake_transom(side=-1.0, n=60):
    """Listen tvers over akterspeilet fra hjoernet paa siden 'side' til
    senterlinjen, med buen P.STRAKE_TRANSOM_RISE (som hull._strake_path),
    13 mm utenfor flaten (halve proud)."""
    xe, yt, zs = strake_corner()
    ys = yt * (1.0 - np.arange(0, n + 1) / n)
    zt = zs + P.STRAKE_TRANSOM_RISE * (1.0 - (ys / yt) ** 2) ** 2
    k = np.sqrt(1.0 + P.TRANSOM_RAKE ** 2)
    pts = np.array([[C.transom_x(z, y) + 0.5 * P.STRAKE_PROUD * k, side * y, z] for y, z in zip(ys, zt)])
    return pts


def strake_full():
    """Babord side -> babord akterspeil -> styrbord akterspeil -> styrbord side."""
    a = strake_side(-1.0)
    b = strake_transom(-1.0)
    cc = strake_transom(1.0)[::-1]
    d = strake_side(1.0)[::-1]
    return np.vstack([a, b, cc[1:], d])


def top_edge(y):
    """Akterspeilets overkant ved halvbredde y: (x, z) (som hull._top_edge)."""
    z = C.deck_z(C.transom_x(950.0, y), y)
    x = C.transom_x(z, y)
    for _ in range(30):
        x = C.transom_x(z, y)
        z1 = C.deck_z(x, y)
        if abs(z1 - z) < 1e-4:
            break
        z = z1
    return x, z


def transom_top(n=81):
    """Akterspeilets overkant tvers over (y fra -ymax til ymax)."""
    xe = strake_corner()[0]
    # overkantens halvbredde: dekkets omriss ved akterspeilet
    ym = None
    for y in np.linspace(1200.0, 0.0, 600):
        x, z = top_edge(y)
        hb = C.deck_half_breadth(x)
        if y <= hb:
            ym = y
            break
    ys = np.linspace(-ym, ym, n)
    return np.array([[top_edge(abs(y))[0], y, top_edge(abs(y))[1]] for y in ys])


def on_transom(cam, u, v, t0=300.0, t1=12000.0):
    """Punktet paa akterspeilsflaten x = transom_x(z, y) som ses i (u, v)."""
    from scipy.optimize import brentq
    o = cam.C
    d = cam.ray(np.array([u]), np.array([v]))[0]
    g = lambda t: (o + t * d)[0] - C.transom_x((o + t * d)[2], (o + t * d)[1])
    ts = np.linspace(t0, t1, 400)
    gv = [g(t) for t in ts]
    for i in range(len(ts) - 1):
        if gv[i] * gv[i + 1] <= 0.0:
            t = brentq(g, ts[i], ts[i + 1])
            return o + t * d
    return None


def keel_mesh():
    return G.keel_mesh(-300.0, 12.0)


def keel_outline_xz():
    return G.keel_outline_xz()


def rudder_mesh():
    return G.rudder_mesh(24)


def rudder_le(z0=None, z1=None, n=40):
    """Rorets forkant (hengsellinja) paa senterlinjen; modellens ror slutter
    ved RUDDER_TOP_Z, over det foelger det ekte roret akterspeilet."""
    z0 = P.RUDDER_BOT_Z if z0 is None else z0
    z1 = P.RUDDER_TOP_Z if z1 is None else z1
    zz = np.linspace(z0, z1, n)
    t = (zz - P.RUDDER_TOP_Z) / (P.RUDDER_BOT_Z - P.RUDDER_TOP_Z)
    return np.c_[P.RUDDER_X + P.RUDDER_RAKE * t, np.zeros(n), zz]


def hull_mesh(n_st=220, nsec=60):
    return U.hull_mesh(n_st, nsec)


if __name__ == "__main__":
    sc = strake_corner()
    print("listens hjoerne (x, y, z):", np.round(sc, 1), " transom_x(z=0):", C.transom_x(0.0))
    for z in (900, 850, 804, 700, 600, 500, 400, 300, 200, 150, 100, 50, 0, -50, -100, -200, -300, -400):
        k = corner_y(float(z))
        print(f"z {z:5d}: hjoerne {'-' if k is None else '%.0f, %.0f' % k}")
    tt = transom_top()
    print("overkant: y", tt[0, 1].round(), "z hjoerne", tt[0, 2].round(), "z midt", tt[len(tt) // 2, 2].round(),
          "x midt", tt[len(tt) // 2, 0].round())
    ko = keel_outline_xz()
    print("kjol omriss z min", ko[:, 1].min(), "x ved bunn", ko[np.argmin(ko[:, 1]), 0])
    print("ror forkant topp", rudder_le()[-1], "bunn", rudder_le()[0], "TE", P.RUDDER_TE_X)
    print("sheer ved 7900:", C.sheer_z(7900.0), "strake ved 7900", C.strake_z(7900.0))
