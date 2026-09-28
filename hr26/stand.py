"""Stativ: to vugger som foelger skrogformen, og en langbjelke som binder dem.

Vuggene freses ut etter skrogets egne spant med en liten klaring, saa de
sitter noyaktig men ikke i press. Stasjonene er valgt foran og bak kjolen,
slik at vuggene gaar klar av den.
"""
from __future__ import annotations

import math

import cadquery as cq

from . import curves as C
from . import params as P

CLEAR = 0.25 * P.SCALE          # klaring mellom skrog og vugge (0,25 mm)


def _offset_section(x: float, clear: float, n: int = 30):
    """Spantet ved x, forskjovet utover langs normalen."""
    pts = C.section(x, n=n)
    pts = pts + [(y, z) for (y, z) in C.deck_arc(x)[1:]]
    out = []
    for i, (y, z) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        ty, tz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ty, tz) or 1.0
        ny, nz = tz / L, -ty / L          # normal, peker utover paa styrbord
        out.append((y + ny * clear, z + nz * clear))
    return out


def _hull_cutter(x: float, thickness: float, clear: float) -> cq.Workplane:
    """Et prisme med skrogets tverrsnitt, brukt til aa frese ut vuggen."""
    prof = _offset_section(x, clear)
    stb = [cq.Vector(0.0, y, z) for (y, z) in prof]
    port = [cq.Vector(0.0, -y, z) for (y, z) in reversed(prof)]
    edges = [cq.Edge.makeSpline(stb)]
    if (stb[-1] - port[0]).Length > 1e-6:
        edges.append(cq.Edge.makeLine(stb[-1], port[0]))
    edges.append(cq.Edge.makeSpline(port))
    if (port[-1] - stb[0]).Length > 1e-6:
        edges.append(cq.Edge.makeLine(port[-1], stb[0]))
    face = cq.Face.makeFromWires(cq.Wire.assembleEdges(edges))
    solid = cq.Solid.extrudeLinear(face, cq.Vector(3.0 * thickness, 0.0, 0.0))
    return cq.Workplane("XY").newObject([solid]).translate(
        (x - 1.5 * thickness, 0.0, 0.0)
    )


def cradle(x: float, thickness: float | None = None) -> cq.Workplane:
    """En vugge ved stasjon x."""
    t = P.STAND_THICK if thickness is None else thickness
    hb = C.deck_half_breadth(x)
    zb = C.bottom_z(x)
    top = zb + 0.55 * (C.sheer_z(x) - zb)
    base_z = -P.DRAFT - P.STAND_CLEAR

    block = (
        cq.Workplane("XY")
        .workplane(offset=base_z)
        .rect(t, 2.0 * hb + 24.0 * P.SCALE)
        .extrude(top - base_z)
        .edges("|X")
        .fillet(5.0 * P.SCALE)
        .translate((x, 0.0, 0.0))
    )
    block = block.cut(_hull_cutter(x, t, CLEAR))

    # spor i bunnen som vuggen treas ned paa bjelketappen
    slot = (
        cq.Workplane("XY")
        .workplane(offset=base_z - 1.0)
        .rect(t + 2.0 * 0.2 * P.SCALE, 24.0 * P.SCALE + 2.0 * 0.2 * P.SCALE)
        .extrude(5.0 * P.SCALE + 1.0)
        .translate((x, 0.0, 0.0))
    )
    return block.cut(slot)


def beam() -> cq.Workplane:
    """Langbjelke med tapper som vuggene treas ned paa."""
    x0, x1 = P.STAND_STATIONS
    length = abs(x1 - x0) + 34.0 * P.SCALE
    h = 9.0 * P.SCALE
    base_z = -P.DRAFT - P.STAND_CLEAR - h
    b = (
        cq.Workplane("XY")
        .workplane(offset=base_z)
        .rect(length, P.STAND_BASE_W)
        .extrude(h)
        .edges("|Z")
        .fillet(7.0 * P.SCALE)
        .translate((0.5 * (x0 + x1), 0.0, 0.0))
    )
    # lettelseshull slik at bjelken ikke blir en massiv kloss
    b = b.cut(
        cq.Workplane("XY")
        .workplane(offset=base_z + 2.0 * P.SCALE)
        .rect(length - 26.0 * P.SCALE, P.STAND_BASE_W - 20.0 * P.SCALE)
        .extrude(h)
        .edges("|Z")
        .fillet(8.0 * P.SCALE)
        .translate((0.5 * (x0 + x1), 0.0, 0.0))
    )
    for x in (x0, x1):
        b = b.union(
            cq.Workplane("XY")
            .workplane(offset=base_z + h)
            .rect(P.STAND_THICK, 24.0 * P.SCALE)
            .extrude(5.0 * P.SCALE)
            .translate((x, 0.0, 0.0))
        )
    return b


def parts() -> dict:
    out = {}
    for i, x in enumerate(P.STAND_STATIONS, start=1):
        out[f"stativ-vugge{i}"] = cradle(x)
    out["stativ-bjelke"] = beam()
    return out
