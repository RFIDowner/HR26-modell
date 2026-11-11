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

    Akterspeilet heller TRANSOM_RAKE med toppen akterover og er svakt buet i
    plan (TRANSOM_CAMBER_R). Kuttet av skroget (offset = 0) runder ogsaa
    hjoernene mot skrogsidene (_rounded_cutter). `offset` flytter flaten saa
    mange mm akterover (navnet i relieff) og gir det enkle prismet.
    """
    if offset == 0.0 and P.TRANSOM_CORNER_L > 0.0:
        try:
            return _rounded_cutter()
        except Exception as exc:  # pragma: no cover - faller tilbake til skarpe hjoerner
            print(f"  advarsel: rundede akterspeilhjoerner feilet ({exc}); bruker skarpe")
    return _plain_cutter(offset)


def _plain_cutter(offset: float = 0.0) -> cq.Workplane:
    """Et prisme med buet forkant (akterspeilets kamber i plan), dreid om en
    tverrgaaende akse i DWL saa flaten heller som akterspeilet."""
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


