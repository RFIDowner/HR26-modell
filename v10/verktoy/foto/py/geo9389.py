"""3D-trekk fra modellen til kameraet for IMG_9389 (3/4 forfra, styrbord, lavt).

Bare ting trinn 5 (forkroppen under vann) ikke flytter: fenderlisten,
vannlinjestripen paa siden, vinduets ender, akterspeilets hjoerne (silhuett),
kjolen (A._KeelProfile, 240 mm tykk, fas i bunnen) og roret. Ingen CAD: kjol
og ror bygges som stablede profiler (appendages._foil) i et trekantnett.
Tilpasset fra geo9387.py (babord), her styrbord: y > 0.
"""
import numpy as np

import common as c
import uwlib as U

P, C = c.P, c.C
SIDE = +1.0          # styrbord

_SEC = {}


def section(x, n=160):
    k = (round(float(x), 3), n)
    s = _SEC.get(k)
    if s is None:
        s = np.asarray(C.section(float(x), n), float)
        if len(_SEC) > 20000:
            _SEC.clear()
        _SEC[k] = s
    return s


def side_y(x, z):
    """Skrogets halvbredde i hoeyden z ved stasjon x (fra C.section)."""
    s = section(x)
    zz = s[:, 1]
    i0 = int(np.argmax(zz > zz[0] + 1.0))          # forbi en ev. flat bunn
    zs, ys = zz[i0:], s[i0:, 0]
    o = np.argsort(zs)
    return float(np.interp(z, zs[o], ys[o], left=np.nan, right=np.nan))


def strake_end_x():
    lo, hi = 6000.0, P.LOA
    for _ in range(40):
        m = 0.5 * (lo + hi)
        z = C.strake_z(m)
        y = side_y(m, z)
        if np.isfinite(y) and m < C.transom_x(z, y):
            lo = m
        else:
            hi = m
    return lo


def strake3(x0=500.0, x1=None, n=260, dz=0.0):
    """Fenderlistens senter (eller kant: dz = +-29) paa styrbord side."""
    if x1 is None:
        x1 = strake_end_x()
    xs = np.linspace(x0, x1, n)
    out = []
    for x in xs:
        z = C.strake_z(x) + dz
        y = side_y(x, z)
        out.append((x, SIDE * (y + 0.5 * P.STRAKE_PROUD), z))
    return np.array(out)


def zline3(zfun, x0, x1, n=200):
    """Linje i hoeyden zfun(x) paa styrbord skrogside, fra x0 til x1 (stopper
    ved akterspeilet)."""
    xs = np.linspace(x0, x1, n)
    out = []
    for x in xs:
        z = float(zfun(x))
        y = side_y(x, z)
        if not np.isfinite(y):
            continue
        if x > C.transom_x(z, y):
            break
        out.append((x, SIDE * y, z))
    return np.array(out)


def bt_top_z(x, z0=146.0, z1=125.0):
    """Blaa overkant (IMG_9370): 146 ved x 1000, 125 fra x 5500."""
    t = np.clip((np.asarray(x, float) - 1000.0) / 4500.0, 0.0, 1.0)
    return z0 + (z1 - z0) * t


def window_ends():
    """Vinduets forreste og bakerste punkt (ytre ramme) slik modellen har
    det (se geo9387.window_ends), styrbord."""
    rf, ra = P.WIN_RAKE
    x0 = P.WIN_X0 + 0.5 * rf * 0.6
    zlo0 = C.strake_z(x0) + P.WIN_ABOVE_STRAKE
    zhi0 = C.sheer_z(x0) - P.WIN_BELOW_DECK
    zm = 0.5 * (zlo0 + zhi0)
    f = (x0, SIDE * side_y(x0, zm), zm)
    x1 = P.WIN_X1 - 15.0
    z1 = C.strake_z(x1) + P.WIN_ABOVE_STRAKE + 25.0
    a = (x1, SIDE * side_y(x1, z1), z1)
    return np.array([f, a])


def window_lower3(n=60):
    """Vinduets underkant (ytre ramme) fra forenden til akterenden."""
    xs = np.linspace(P.WIN_X0, P.WIN_X1, n)
    out = []
    for x in xs:
        z = C.strake_z(x) + P.WIN_ABOVE_STRAKE
        out.append((x, SIDE * side_y(x, z), z))
    return np.array(out)


def transom_corner3(z0=-200.0, z1=None, n=60):
    """Akterspeilets hjoerne paa styrbord side: der siden moeter akterspeilet."""
    if z1 is None:
        z1 = C.sheer_z(P.LOA)
    out = []
    for z in np.linspace(z0, z1, n):
        lo, hi = 6500.0, P.LOA + 200.0
        for _ in range(40):
            m = 0.5 * (lo + hi)
            y = side_y(m, z)
            if np.isfinite(y) and m < C.transom_x(z, y):
                lo = m
            else:
                hi = m
        y = side_y(lo, z)
        if np.isfinite(y):
            out.append((lo, SIDE * y, z))
    return np.array(out)


# ---------------------------------------------------------------- kjol og ror som nett
def _stack_mesh(slices):
    Rr = np.array(slices)
    ns, nr, _ = Rr.shape
    V = Rr.reshape(-1, 3)
    idx = np.arange(ns * nr).reshape(ns, nr)
    a = idx[:-1, :]; b = np.roll(idx[:-1, :], -1, axis=1)
    cc = idx[1:, :]; d = np.roll(idx[1:, :], -1, axis=1)
    F = np.r_[np.c_[a.ravel(), b.ravel(), d.ravel()], np.c_[a.ravel(), d.ravel(), cc.ravel()]]
    for ring in (0, ns - 1):
        i0 = idx[ring, 0]
        fan = np.c_[np.full(nr - 2, i0), idx[ring, 1:-1], idx[ring, 2:]]
        F = np.r_[F, fan]
    return V, F


_KEEL = {}


def keel_mesh(z_top=-300.0, dz=12.0, thick=None):
    """Kjolen som stablede profiler fra z_top ned til bunnen, med 45 graders
    fas i bunnkanten. Hulkilen mot skroget (i profil) er med i for- og
    bakkanten (A._KeelProfile)."""
    key = (z_top, dz, thick)
    if key in _KEEL:
        return _KEEL[key]
    from hr26 import appendages as A
    k = A._KeelProfile()
    zb = k.zb
    cf = P.KEEL_BOT_CHAMFER
    zs = list(np.arange(z_top, zb + cf, -dz)) + list(np.linspace(zb + cf, zb, 5))
    slices = []
    for z in zs:
        le, te = k.edges(z)
        th = P.KEEL_TIP_T if thick is None else thick
        e = z - zb
        if e < cf:
            th -= 2.0 * (cf - e)
        th = max(th, 4.0)
        pts = np.array(A._foil(te - le, th, n=30))
        slices.append(np.c_[le + pts[:, 0], pts[:, 1], np.full(len(pts), z)])
    _KEEL[key] = _stack_mesh(slices)
    return _KEEL[key]


def keel_outline_xz():
    from hr26 import appendages as A
    return np.array(A.keel_outline())


def rudder_mesh(n=24):
    from hr26 import appendages as A
    slices = []
    for i in range(n + 1):
        t = i / n
        z = P.RUDDER_TOP_Z + (P.RUDDER_BOT_Z - P.RUDDER_TOP_Z) * t
        le = P.RUDDER_X + P.RUDDER_RAKE * t
        ch = P.RUDDER_TE_X - le
        th = P.RUDDER_T * (1.0 - 0.28 * t)
        pts = np.array(A._foil(ch, th, n=20))
        slices.append(np.c_[le + pts[:, 0], pts[:, 1], np.full(len(pts), z)])
    return _stack_mesh(slices)


def stem_top3(z0=300.0, z1=1000.0, n=60):
    (xa, za), (xb, zb) = P.STEM_LINE
    zz = np.linspace(z0, z1, n)
    xx = xa + (zz - za) * (xb - xa) / (zb - za)
    return np.c_[xx, np.zeros(n), zz]


def upper_hull_mesh(z_min=300.0, n_st=200):
    """Skrogets oevre del (over z_min) med avrundet dekkskant (C.section_parts)."""
    xs = U.station_list(n_st)
    rings = []
    for x in xs:
        sp = C.section_parts(float(x), 20, 9, 15)
        side = sp["side"]
        side = side[side[:, 1] >= z_min] if (side[:, 1] >= z_min).sum() >= 2 else side[-2:]
        s = np.r_[0, np.cumsum(np.hypot(*np.diff(side, axis=0).T))]
        t = np.linspace(0, s[-1], 12)
        side = np.c_[np.interp(t, s, side[:, 0]), np.interp(t, s, side[:, 1])]
        prof = np.vstack([side, sp["corner"][1:], sp["deck"][1:-1]])
        prt = np.vstack([sp["corner"][::-1], side[::-1]]) * np.array([-1.0, 1.0])
        ring = np.vstack([prof, prt[:-1]])
        rings.append(np.c_[np.full(len(ring), float(x)), ring])
    Rr = np.array(rings)
    xt = U.transom_x(Rr[..., 2], Rr[..., 1])
    Rr[..., 0] = np.minimum(Rr[..., 0], xt)
    return U.rings_to_mesh(Rr)


def mesh_outline_px(cam, V, F, step=4):
    """Modellens silhuett som punkter (u, v): min/max per rad og per kolonne."""
    rows = np.arange(0, cam.H, step, dtype=float)
    cols = np.arange(0, cam.W, step, dtype=float)
    lo, hi = U.row_extents(cam, V, F, rows)
    clo, chi = U.row_extents(cam, V, F, cols, axis="col")
    pts = []
    for r, a, b in zip(rows, lo, hi):
        if np.isfinite(a):
            pts += [(a, r), (b, r)]
    for cc, a, b in zip(cols, clo, chi):
        if np.isfinite(a):
            pts += [(cc, a), (cc, b)]
    return np.array(pts)
