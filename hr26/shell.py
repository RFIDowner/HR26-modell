"""Uthuling av skroget.

Skroget printes staaende med kjolen ned. Et helt aapent hulrom ville gitt
dekket ingenting aa hvile paa, saa hulrommet deles i kamre av tynne
tverrspant. Spantene printes som rette vegger og baerer dekket.

Hulrommet bygges som ett kammer om gangen og trekkes fra hver for seg.
Det er baade raskere og langt mindre minnekrevende enn aa lage ett stort
hulrom og saa skjaere spor i det.
"""
from __future__ import annotations

import cadquery as cq

from . import curves as C
from . import params as P


def _inner_wire(x: float, wall: float, deck_t: float, n_pts: int = 20):
    pts = C.section_inner(x, wall, deck_t, n=n_pts)
    if pts is None:
        return None
    stb = [cq.Vector(x, y, z) for (y, z) in pts]
    port = [cq.Vector(x, -y, z) for (y, z) in reversed(pts)]
    arc = [cq.Vector(x, y, z) for (y, z) in C.deck_arc_inner(x, wall, deck_t)]
    edges = [cq.Edge.makeSpline(stb)]
    if len(arc) > 2:
        edges.append(cq.Edge.makeSpline([stb[-1]] + arc[1:-1] + [port[0]]))
    elif (stb[-1] - port[0]).Length > 1e-6:
        edges.append(cq.Edge.makeLine(stb[-1], port[0]))
    edges.append(cq.Edge.makeSpline(port))
    if (port[-1] - stb[0]).Length > 1e-6:
        edges.append(cq.Edge.makeLine(port[-1], stb[0]))
    return cq.Wire.assembleEdges(edges)


def bulkhead_stations():
    """x-posisjonene til de innvendige spantene."""
    xs = []
    x = P.VOID_FWD + P.RIB_PITCH
    while x < P.LOA - P.VOID_AFT - 0.3 * P.RIB_PITCH:
        xs.append(x)
        x += P.RIB_PITCH
    return xs


def compartments(wall: float | None = None, deck_t: float | None = None, per_bay: int = 4):
    """Hulrommet som en liste kamre, ett mellom hvert par av spant."""
    wall = P.HULL_WALL if wall is None else wall
    deck_t = P.DECK_THICK if deck_t is None else deck_t
    half = 0.5 * P.RIB_THICK

    bounds = [P.VOID_FWD] + bulkhead_stations() + [P.LOA - P.VOID_AFT]
    out = []
    for i in range(len(bounds) - 1):
        a = bounds[i] + (half if i else 0.0)
        b = bounds[i + 1] - (half if i + 1 < len(bounds) - 1 else 0.0)
        if b - a < 4.0 * P.SCALE:
            continue
        xs = [a + (b - a) * j / (per_bay - 1) for j in range(per_bay)]
        wires = [w for w in (_inner_wire(x, wall, deck_t) for x in xs) if w is not None]
        if len(wires) < 2:
            continue
        try:
            out.append(cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=False)]))
        except Exception:  # pragma: no cover - degenerert kammer hoppes over
            continue
    return out


def hollow(solid: cq.Workplane, log=None, **kw) -> cq.Workplane:
    """Trekker kamrene fra en ferdig sammensatt modell."""
    bays = compartments(**kw)
    for i, c in enumerate(bays, start=1):
        solid = solid.cut(c)
        if log:
            log(f"    kammer {i}/{len(bays)}")
    return solid.clean()


def material_cm3(solid: cq.Workplane) -> float:
    """Plastforbruk i modellskala, cm3."""
    return solid.val().Volume() / P.SCALE ** 3 / 1000.0
