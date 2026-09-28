"""Skroget: loftet gjennom spant fra data/hull_stations.csv.

Spantene lukkes oppe av dekksbuen, slik at skroget kommer ut av loftet
med ferdig buet dekk - ingen ekstra boolsk operasjon som kan feile.
"""
from __future__ import annotations

import cadquery as cq

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


def rubbing_strake(n: int = 60) -> cq.Workplane:
    """Fenderlist: en list som foelger dekkskanten hele veien rundt."""
    path_pts = []
    for i in range(n + 1):
        x = P.LOA * i / n
        x = min(max(x, 3.0), P.LOA - 3.0)
        z = C.sheer_z(x) - P.STRAKE_DROP
        y = C.deck_half_breadth(x)
        path_pts.append((x, y, z))

    sweeps = []
    for sign in (1, -1):
        pts = [cq.Vector(x, sign * y, z) for (x, y, z) in path_pts]
        path = cq.Wire.assembleEdges([cq.Edge.makeSpline(pts)])
        prof = (
            cq.Workplane("YZ")
            .center(sign * path_pts[0][1], path_pts[0][2])
            .rect(P.STRAKE_PROUD * 2, P.STRAKE_H)
        )
        try:
            sweeps.append(
                cq.Workplane("XY")
                .newObject([prof.val()])
                .sweep(cq.Workplane("XY").newObject([path]), isFrenet=True)
            )
        except Exception:  # pragma: no cover - degenerert sveip
            pass
    if not sweeps:
        return cq.Workplane("XY")
    out = sweeps[0]
    for s in sweeps[1:]:
        out = out.union(s)
    return out
