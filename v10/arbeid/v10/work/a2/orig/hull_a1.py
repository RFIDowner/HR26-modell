"""Skroget: loftet gjennom spant fra data/hull_stations.csv.

Spantene lukkes oppe av dekksbuen, slik at skroget kommer ut av loftet
med ferdig buet dekk - ingen ekstra boolsk operasjon som kan feile.
Hekken er rundet i plan; loften gaar forbi akterspeilet, og alt aktenfor
akterspeilets hellende, svakt buede flate kappes bort etterpaa.
"""
from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from . import curves as C
from . import params as P

STERN_STATIONS = (7850.0, 7910.0)   # ekstra spant der hekken runder av


def _section_wire(x: float, n_pts: int = 24) -> cq.Wire:
    """Lukket, speilsymmetrisk spant ved stasjon x.

    Wiren bestaar av: spline styrbord (kjol -> dekkskant), rett linje tvers
    over dekksaapningen, spline babord (dekkskant -> kjol).
    """
    pts = C.section(x, n=n_pts)
    stb = [cq.Vector(x, y, z) for (y, z) in pts]
    port = [cq.Vector(x, -y, z) for (y, z) in reversed(pts)]
    arc = [cq.Vector(x, y, z) for (y, z) in C.deck_arc(x)]

    edges = [cq.Edge.makeSpline(stb)]
    if len(arc) > 2 and (arc[0] - arc[-1]).Length > 1e-6:
        edges.append(cq.Edge.makeSpline([stb[-1]] + arc[1:-1] + [port[0]]))
    elif (stb[-1] - port[0]).Length > 1e-6:
        edges.append(cq.Edge.makeLine(stb[-1], port[0]))
    edges.append(cq.Edge.makeSpline(port))
    if (port[-1] - stb[0]).Length > 1e-6:
        edges.append(cq.Edge.makeLine(port[-1], stb[0]))
    return cq.Wire.assembleEdges(edges)


def transom_cutter(offset: float = 0.0) -> cq.Workplane:
    """Alt aktenfor akterspeilet.

    Et prisme med buet forkant (akterspeilets kamber i plan), dreid om en
    tverrgaaende akse i DWL saa flaten heller som akterspeilet. `offset`
    flytter flaten saa mange mm akterover (brukes til navnet i relieff).
    """
    R = P.TRANSOM_CAMBER_R
    xw = P.TRANSOM_WL_X + offset
    half = 2400.0
    sag = R - math.sqrt(R * R - half * half)
    prism = (
        cq.Workplane("XY")
        .workplane(offset=-4000.0)
        .moveTo(xw - sag, -half)
        .threePointArc((xw, 0.0), (xw - sag, half))
        .lineTo(xw + 3000.0, half)
        .lineTo(xw + 3000.0, -half)
        .close()
        .extrude(8000.0)
    )
    ang = math.degrees(math.atan(P.TRANSOM_RAKE))
    return prism.rotate((xw, 0.0, 0.0), (xw, 1.0, 0.0), ang)


def hull_solid(n_stations: int = 34, n_pts: int = 24) -> cq.Solid:
    """Skroget som et lukket volum, uten kjol og ror, kappet av akterspeilet."""
    xs = C.stations(n_stations)
    # unnga degenererte spant helt i endene; tettere spant rundt hekken
    xs = [x for x in xs if 6.0 < x < P.LOA - 4.0]
    xs = sorted(set([4.0] + xs + list(STERN_STATIONS) + [P.LOA - 2.0]))
    xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 8.0]

    wires = [_section_wire(x, n_pts) for x in xs]
    loft = cq.Solid.makeLoft(wires, ruled=False)
    cut = cq.Workplane("XY").newObject([loft]).cut(transom_cutter())
    solids = cut.val().Solids()
    if len(solids) != 1:
        raise RuntimeError(f"akterspeilkuttet ga {len(solids)} solider")
    return solids[0]


def hull(n_stations: int = 34) -> cq.Workplane:
    """Skrog kappet ved dekkskanten, med baug og hekk lukket."""
    s = hull_solid(n_stations)
    return cq.Workplane("XY").newObject([s])


# ------------------------------------------------------------- fenderlist
def _side_frame(x: float, zc: float):
    """Skrogsidens halvbredde ved stasjon x i hoyden zc, og sidens normal
    utover i spantets plan (ny, nz)."""
    sec = np.array(C.section(x, 60))
    yc = float(np.interp(zc, sec[:, 1], sec[:, 0]))
    y_lo = float(np.interp(zc - 25.0, sec[:, 1], sec[:, 0]))
    y_hi = float(np.interp(zc + 25.0, sec[:, 1], sec[:, 0]))
    ty, tz = y_hi - y_lo, 50.0                 # tangent oppover langs siden
    L = math.hypot(ty, tz)
    return yc, (tz / L, -ty / L)


def _strake_path(n_side: int = 48, n_transom: int = 12):
    """Listens senterlinje paa styrbord side: liste av (punkt, normal utover),
    fra STRAKE_X0 langs skrogsiden til akterspeilet og saa tvers over
    akterspeilet til senterlinjen. Hoyden foelger strake_z."""
    def inside(x):
        zc = C.strake_z(x)
        yc, _ = _side_frame(x, zc)
        return x < C.transom_x(zc, yc)

    # der siden treffer akterspeilet (halvering)
    lo, hi = P.STRAKE_X0, P.LOA - 2.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if inside(mid):
            lo = mid
        else:
            hi = mid
    x_m = lo
    xs = [x for x in C.stations(n_side) if P.STRAKE_X0 < x < x_m - 30.0]
    xs = [P.STRAKE_X0] + xs + [x_m]

    out = []
    for x in xs:
        zc = C.strake_z(x)
        yc, (ny, nz) = _side_frame(x, zc)
        out.append(((x, yc, zc), (0.0, ny, nz)))

    # tvers over akterspeilet, i listens hoyde ved hjornet
    zc = C.strake_z(x_m)
    y_m = out[-1][0][1]
    phi = math.atan(P.TRANSOM_RAKE)
    for i in range(1, n_transom + 1):
        y = y_m * (1.0 - i / n_transom)
        psi = math.asin(min(y / P.TRANSOM_CAMBER_R, 1.0))
        n = (math.cos(psi) * math.cos(phi), math.sin(psi), -math.cos(psi) * math.sin(phi))
        out.append(((C.transom_x(zc, y), y, zc), n))
    return out


def rubbing_strake(n_stations: int = 48) -> cq.Workplane:
    """Fenderlist: en list langs skrogsiden og rundt hekken, halvt begravd.

    Loftet (ruled) gjennom rektangler STRAKE_H x 2 * STRAKE_PROUD som staar
    vinkelrett paa listens senterlinje og dreid etter skrogets normal der,
    saa listen stikker like langt ut ogsaa der siden faller ut. Ett
    sammenhengende volum fra babord forende, rundt akterspeilet, til
    styrbord forende.
    """
    stb = _strake_path(n_stations)
    port = [((x, -y, z), (nx, -ny, nz)) for (x, y, z), (nx, ny, nz) in reversed(stb[:-1])]
    path = stb + port
    pts = np.array([p for p, _ in path])
    nrm = np.array([n for _, n in path])
    tan = np.gradient(pts, axis=0)
    tan /= np.linalg.norm(tan, axis=1, keepdims=True)
    half_h = 0.5 * P.STRAKE_H

    wires = []
    for c, t, n in zip(pts, tan, nrm):
        # normalen vinkelrett paa tangenten; "opp" vinkelrett paa begge
        n = n - np.dot(n, t) * t
        n /= np.linalg.norm(n)
        u = np.cross(n, t)
        u /= np.linalg.norm(u)
        if u[2] < 0.0:
            u = -u
        corners = [cq.Vector(*(c + a * P.STRAKE_PROUD * n + b * half_h * u))
                   for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        wires.append(cq.Wire.makePolygon(corners + [corners[0]]))
    solid = cq.Solid.makeLoft(wires, ruled=True)
    return cq.Workplane("XY").newObject([solid])
