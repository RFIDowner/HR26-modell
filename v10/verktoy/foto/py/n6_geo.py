"""3D-trekk fra modellen (arbeidstreet) til kameraet for «nye (6).jpeg»
(styrbord laaring, lavt kamera). Ingen CAD bygges; hr26.hull importeres bare
for listens bane (hull._strake_path), som er ren numpy.

Bildet viser styrbord side (y > 0 i modellen: x akterover, z opp). Baaten er
symmetrisk, saa det betyr ingenting for maalene om bildet skulle vaere speilet.
"""
import numpy as np

import common as c
import uwlib as U
import geo9374 as G

geo_model = G.use_model(None)          # arbeidstreet (modellen eieren ser, V10 trinn 5)
P = c.P
C = c.C


class Cam(G.Cam9374):
    """geo9374.Cam9374 (uwlib.Cam + hovedpunkt du, dv og radial k1) med i
    tillegg radial k2: u_d = c + f x (1 + k1 r^2 + k2 r^4)."""

    def __init__(self, p, W, H, du=0.0, dv=0.0, k1=0.0, k2=0.0, asp=1.0):
        super().__init__(p, W, H, du=du, dv=dv, k1=k1, asp=asp)
        self.k2 = k2

    def project(self, X):
        Q = (np.asarray(X, float) - self.C) @ self.R.T
        z = np.maximum(Q[:, 2], 1e-6)
        a, b = Q[:, 0] / z, Q[:, 1] / z
        r2 = a * a + b * b
        s = 1.0 + self.k1 * r2 + self.k2 * r2 * r2
        a, b = a * s, b * s
        return self.f * a + self.cx, self.f * self.asp * b + self.cy, Q[:, 2]

    def ray(self, u, v):
        """Retning (verdenskoordinater) gjennom piksel (u, v): fortegningen
        inverteres med fastpunkt-iterasjon."""
        ad = (np.asarray(u, float) - self.cx) / self.f
        bd = (np.asarray(v, float) - self.cy) / (self.f * self.asp)
        a, b = ad.copy(), bd.copy()
        for _ in range(30):
            r2 = a * a + b * b
            s = 1.0 + self.k1 * r2 + self.k2 * r2 * r2
            a, b = ad / s, bd / s
        d = np.stack([a, b, np.ones_like(a)], axis=-1) @ self.R
        return d / np.linalg.norm(d, axis=-1, keepdims=True)


def strake_paths():
    """Listens synlige senter (skrogflaten + normal * proud/2): sidedelen
    (x til hjoernet), akterspeilsdelen paa styrbord (fra hjoernet til
    senterlinjen) og speilbildet paa babord (fra senterlinjen til hjoernet)."""
    from hr26 import hull as Hh
    pts, nrm = Hh._strake_path(20.0)
    vis = pts + nrm * (0.5 * P.STRAKE_PROUD)
    # akterspeilsdelen: der banen ligger paa akterspeilsflaten (x ~ transom_x)
    on_tr = np.array([abs(p[0] - C.transom_x(p[2], p[1])) < 3.0 for p in pts])
    k = int(np.argmax(on_tr))                       # foerste punkt paa akterspeilet
    side = vis[:k]
    tr = vis[k:]
    far = tr[::-1].copy()
    far[:, 1] *= -1.0
    return dict(side=side, tr_stbd=tr, tr_port=far, corner_stbd=vis[k],
                corner_port=np.array([vis[k][0], -vis[k][1], vis[k][2]]), path=pts, k=k)


def transom_corner_line(z0=150.0, z1=None, n=40):
    """Det naere (styrbord) akterspeilhjoernet fra z0 til listen: der
    skrogsiden moeter akterspeilsflaten. Halvbredden tas fra G.side_y ved
    x = transom_x (iterert)."""
    if z1 is None:
        z1 = float(C.strake_z(7850.0)) - 30.0
    out = []
    for z in np.linspace(z0, z1, n):
        x = C.transom_x(z, 0.0)
        y = 0.0
        for _ in range(30):
            y = G.side_y(x, z)
            if not np.isfinite(y):
                break
            xn = C.transom_x(z, y)
            if abs(xn - x) < 0.2:
                break
            x = xn
        if np.isfinite(y):
            out.append((x, y, z))
    return np.array(out)


def keel_mesh():
    return G.keel_mesh(-300.0, 12.0)


def rudder_mesh():
    return G.rudder_mesh(24)


def hull_mesh(n_st=220, nsec=60):
    return U.hull_mesh(n_st, nsec)


def window_outline(n=60):
    """Vinduets ytre ramme paa styrbord side slik modellen har det (hjoernene
    fra P.WIN_*): underkant strake + WIN_ABOVE_STRAKE, overkant sheer -
    WIN_BELOW_DECK, endene skraa (WIN_RAKE). Gir (n,3) rundt omkretsen."""
    rf, ra = P.WIN_RAKE
    x0, x1 = P.WIN_X0, P.WIN_X1
    xs_b = np.linspace(x0, x1, n)
    xs_t = np.linspace(x0 + rf, x1 - ra, n)
    zb = np.array([C.strake_z(x) + P.WIN_ABOVE_STRAKE for x in xs_b])
    zt = np.array([C.sheer_z(x) - P.WIN_BELOW_DECK for x in xs_t])
    bot = [(x, G.side_y(x, z), z) for x, z in zip(xs_b, zb)]
    top = [(x, G.side_y(x, z), z) for x, z in zip(xs_t, zt)]
    pts = np.array(bot + top[::-1] + bot[:1])
    return pts


def window_ends():
    """Vinduets bakerste og forreste punkt (ytre ramme) i modellen, styrbord:
    bakre ende (akterover = x stoerst) og fremre ende. Samme definisjon som
    geo9374.window_ends, speilet."""
    w = G.window_ends()
    w[:, 1] *= -1.0
    return w      # [fwd, aft]
