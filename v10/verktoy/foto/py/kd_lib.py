"""Dekkskant-maaleren (kd_, 13.11.2026): felles hjelpere.

Modellens 3D-linjer paa en skrogside (side=-1 babord, +1 styrbord), uten
CadQuery: dekkskanten (sheer), fenderlisten, vinduets omriss, ruffens fot og
takkant, cockpitkarmen. Ruffens bredde og tak er kopiert enkelt fra
hr26.deckhouse (den importerer cadquery).
"""
import math

import numpy as np

import common as c
import geo9374 as G

G.use_model(None)
P, C = c.P, c.C


def sheer3(x0=200.0, x1=7900.0, n=300, side=-1, dz=0.0, zfun=None):
    """Dekkskanten: (x, side*deck_half_breadth, sheer_z [+dz])."""
    xs = np.linspace(x0, x1, n)
    zf = zfun or C.sheer_z
    return np.array([(x, side * C.deck_half_breadth(x), zf(x) + dz) for x in xs])


def strake3(x0=450.0, x1=None, n=300, side=-1):
    S = G.strake3(x0, x1, n)
    S[:, 1] *= -side
    return S


def coach_half_width(x):
    w = max(P.COACH_MIN_HALF_W, C.deck_half_breadth(x) - P.SIDEDECK)
    R = P.COACH_FRONT_R
    if x < P.STEP_X0 + R:
        u = (P.STEP_X0 + R - x) / R
        w *= math.sqrt(max(0.0, 1.0 - u * u))
    return w


def deck_z(x, y):
    hb = C.deck_half_breadth(x)
    return C.sheer_z(x) + P.DECK_CAMBER * (1.0 - (y / hb) ** 2)


def roof_z(x):
    a = np.array(P.COACH_TOP)
    return float(np.interp(x, a[:, 0], a[:, 1]))


def coach_foot3(x0=2700.0, x1=None, n=120, side=-1):
    x1 = x1 or P.COACH_X1 - P.COACH_RAD
    xs = np.linspace(x0, x1, n)
    return np.array([(x, side * coach_half_width(x), deck_z(x, coach_half_width(x))) for x in xs])


def coach_top3(x0=2700.0, x1=None, n=120, side=-1):
    """Ruffens takkant: sidene heller COACH_SIDE_ANGLE, saa kanten staar inne."""
    x1 = x1 or P.COACH_X1 - P.COACH_RAD
    xs = np.linspace(x0, x1, n)
    out = []
    for x in xs:
        w0 = coach_half_width(x)
        zt = roof_z(x) - P.COACH_ROOF_CAMBER * (w0 / 1500.0) ** 2
        h = zt - deck_z(x, w0)
        w = w0 - h / math.tan(math.radians(P.COACH_SIDE_ANGLE))
        out.append((x, side * w, zt))
    return np.array(out)


def coaming_top3(x0=5700.0, x1=6850.0, n=80, side=-1):
    a = np.array(P.COAMING_TOP_Z)
    fit = np.polyfit(a[:, 0] - a[:, 0].mean(), a[:, 1], 2)
    xs = np.linspace(x0, x1, n)
    out = []
    for x in xs:
        w = max(260.0, min(P.COAMING_HALF_W, C.deck_half_breadth(x) - 200.0))
        out.append((x, side * w, float(np.polyval(fit, x - a[:, 0].mean()))))
    return np.array(out)


def window3(side=-1, n=40):
    """Vinduets ytre omriss (forenklet): underkant listen + WIN_ABOVE_STRAKE,
    overkant dekkskanten - WIN_BELOW_DECK, skraa ender (WIN_RAKE)."""
    rf, ra = P.WIN_RAKE
    xs = np.linspace(P.WIN_X0, P.WIN_X1, n)
    lo = [(x, C.strake_z(x) + P.WIN_ABOVE_STRAKE) for x in xs]
    hi = [(x, C.sheer_z(x) - P.WIN_BELOW_DECK) for x in np.linspace(P.WIN_X0 + rf, P.WIN_X1 - ra, n)]
    pts = lo + hi[::-1] + lo[:1]
    out = []
    for x, z in pts:
        y = G.side_y(x, min(z, C.sheer_z(x) - 5.0))
        out.append((x, side * y, z))
    return np.array(out)


def on_side(x, z, side=-1):
    """Punkt paa skrogsiden ved (x, z); over dekkskanten brukes kantens bredde."""
    zs = C.sheer_z(x)
    y = G.side_y(x, min(z, zs - 3.0))
    if not np.isfinite(y):
        y = C.deck_half_breadth(x)
    return np.array([x, side * y, z])


def solve_xz(cam, u, v, x_guess, side=-1, z_guess=1100.0, it=30):
    """Finn (x, z) paa skrogsiden som projiseres til (u, v) (Gauss-Newton)."""
    x, z = float(x_guess), float(z_guess)
    for _ in range(it):
        p0 = on_side(x, z, side)
        uu, vv, _ = cam.project(p0[None])
        r = np.array([uu[0] - u, vv[0] - v])
        if np.hypot(*r) < 1e-3:
            break
        J = np.zeros((2, 2))
        for k, (dx, dz) in enumerate(((5.0, 0.0), (0.0, 5.0))):
            p1 = on_side(x + dx, z + dz, side)
            u1, v1, _ = cam.project(p1[None])
            J[:, k] = [(u1[0] - uu[0]) / 5.0, (v1[0] - vv[0]) / 5.0]
        d = np.linalg.solve(J, -r)
        d = np.clip(d, -400.0, 400.0)
        x, z = x + d[0], z + d[1]
    return x, z
