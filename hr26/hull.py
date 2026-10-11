"""Skroget: loftet gjennom spant fra data/hull_stations.csv.

Spantene lukkes oppe av dekksbuen, slik at skroget kommer ut av loftet
med ferdig buet dekk - ingen ekstra boolsk operasjon som kan feile.
"""
from __future__ import annotations

import cadquery as cq
import numpy as np

from . import curves as C
from . import params as P


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


def hull_solid(n_stations: int = 34, n_pts: int = 24) -> cq.Solid:
    """Skroget som et lukket volum, uten kjol og ror."""
    xs = C.stations(n_stations)
    # unnga degenererte spant helt i endene
    xs = [x for x in xs if 6.0 < x < P.LOA - 4.0]
    xs = [4.0] + xs + [P.LOA - 2.0]

    wires = [_section_wire(x, n_pts) for x in xs]
    solid = cq.Solid.makeLoft(wires, ruled=False)
    return solid


def hull(n_stations: int = 34) -> cq.Workplane:
    """Skrog kappet ved dekkskanten, med baug og hekk lukket."""
    s = hull_solid(n_stations)
    return cq.Workplane("XY").newObject([s])


def rubbing_strake(n_stations: int = 40) -> cq.Workplane:
    """Fenderlist: en list langs skrogsiden, halvt begravd i skroget.

    Loftet gjennom rektangler (STRAKE_H x 2 * STRAKE_PROUD) som staar
    vinkelrett paa skrogsiden ved listens hoyde, saa listen stikker like
    langt ut ogsaa der siden faller ut. Rette linjer mellom stasjonene
    (ruled), en solid per side. Rundt hekken gaar den ikke ennaa.
    """
    x_end = P.LOA - 100.0
    xs = [x for x in C.stations(n_stations) if P.STRAKE_X0 < x < x_end]
    xs = [P.STRAKE_X0] + xs + [x_end]
    half_h = 0.5 * P.STRAKE_H

    def corners(x, sign):
        sec = np.array(C.section(x, 60))
        zc = C.strake_z(x)
        yc = float(np.interp(zc, sec[:, 1], sec[:, 0]))
        y_lo = float(np.interp(zc - 25.0, sec[:, 1], sec[:, 0]))
        y_hi = float(np.interp(zc + 25.0, sec[:, 1], sec[:, 0]))
        ty, tz = y_hi - y_lo, 50.0                 # tangent oppover langs siden
        L = (ty * ty + tz * tz) ** 0.5
        ty, tz = ty / L, tz / L
        ny, nz = tz, -ty                           # normal utover
        pts = []
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            y = yc + a * P.STRAKE_PROUD * ny + b * half_h * ty
            z = zc + a * P.STRAKE_PROUD * nz + b * half_h * tz
            pts.append(cq.Vector(x, sign * y, z))
        return pts

    out = None
    for sign in (1, -1):
        wires = [cq.Wire.makePolygon(corners(x, sign) + [corners(x, sign)[0]]) for x in xs]
        solid = cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=True)])
        out = solid if out is None else out.union(solid)
    return out
