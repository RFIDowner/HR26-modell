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


def _bay_stations(a: float, b: float, wall: float, deck_t: float, per_bay: int,
                  tol: float = 8.0, max_n: int = 24):
    """Stasjoner for loften gjennom ett kammer.

    Jevnt fordelt, men fortettet der hulrommets bunn skifter hoyde fort -
    i baugen stiger den bratt opp langs stevnen, og en loft gjennom faa
    stasjoner ville skaaret rett gjennom skrogveggen mellom dem. Det
    halveres til bunnen mellom to stasjoner ligger innenfor `tol` mm av
    den rette linjen mellom dem.
    """
    def zb(x):
        pts = C.section_inner(x, wall, deck_t)
        return None if pts is None else pts[0][1]

    xs = [a + (b - a) * j / (per_bay - 1) for j in range(per_bay)]
    zs = {x: zb(x) for x in xs}
    changed = True
    while changed and len(xs) < max_n:
        changed = False
        out = [xs[0]]
        for x0, x1 in zip(xs, xs[1:]):
            xm = 0.5 * (x0 + x1)
            zm = zb(xm)
            z0, z1 = zs[x0], zs[x1]
            if zm is not None and z0 is not None and z1 is not None \
                    and abs(zm - 0.5 * (z0 + z1)) > tol and x1 - x0 > 20.0:
                zs[xm] = zm
                out.append(xm)
                changed = True
            elif (zm is None) != (z0 is None and z1 is None) and x1 - x0 > 20.0:
                zs[xm] = zm
                out.append(xm)
                changed = True
            out.append(x1)
        xs = out
    return xs


def compartments(wall: float | None = None, deck_t: float | None = None, per_bay: int = 4):
    """Hulrommet som en liste kamre, ett mellom hvert par av spant."""
    wall = (P.HULL_WALL + P.VOID_MARGIN) if wall is None else wall
    deck_t = P.DECK_THICK if deck_t is None else deck_t
    half = 0.5 * P.RIB_THICK

    bounds = [P.VOID_FWD] + bulkhead_stations() + [P.LOA - P.VOID_AFT]
    out = []
    for i in range(len(bounds) - 1):
        a = bounds[i] + (half if i else 0.0)
        b = bounds[i + 1] - (half if i + 1 < len(bounds) - 1 else 0.0)
        if b - a < 4.0 * P.SCALE:
            continue
        w_bay = wall + (P.VOID_BOW_EXTRA if i == 0 else 0.0)
        xs = _bay_stations(a, b, w_bay, deck_t, per_bay)
        wires = [w for w in (_inner_wire(x, w_bay, deck_t) for x in xs) if w is not None]
        if len(wires) < 2:
            continue
        # Fortettede stasjoner ligger ujevnt, og en glatt loft gjennom dem
        # slaar ut i store buer mellom stasjonene. Da brukes rette linjer.
        ruled = len(xs) > per_bay
        try:
            out.append(cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=ruled)]))
        except Exception:  # pragma: no cover - degenerert kammer hoppes over
            continue
    return out


def hollow(solid: cq.Workplane, log=None, keep=(), **kw) -> cq.Workplane:
    """Trekker kamrene fra en ferdig sammensatt modell.

    `keep` er volumer som skal staa igjen massive - cockpitkaret, ellers
    ville uthulingen tatt gulvet og veggene i bronnen, og cockpiten hadde
    aapnet seg rett inn i det hule skroget. De trekkes fra hvert kammer
    foer kammeret trekkes fra modellen.
    """
    bays = compartments(**kw)
    for i, c in enumerate(bays, start=1):
        for k in keep:
            c = c.cut(k)
        solid = solid.cut(c)
        if log:
            log(f"    kammer {i}/{len(bays)}")
    return solid.clean()


def material_cm3(solid: cq.Workplane) -> float:
    """Plastforbruk i modellskala, cm3."""
    return solid.val().Volume() / P.SCALE ** 3 / 1000.0
