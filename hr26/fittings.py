"""Utsparinger i dekket: mastefot, rekkepaaler, pulpit, pushpit, vinsjer.

Alle hull er dimensjonert for 1,5 mm messingtraad (P.STANCHION_D) med litt
klaring, slik at traaden sitter stramt uten aa sprenge dekket.
"""
from __future__ import annotations

import math

import cadquery as cq

from . import curves as C
from . import deckhouse as D
from . import params as P

CLEAR = 0.10 * P.SCALE          # klaring paa hulldiameter (0,10 mm i modell)
HOLE_DEPTH = 7.0 * P.SCALE      # 7 mm dypt i modellen


def _pin_hole(x: float, y: float, dia: float, depth: float = HOLE_DEPTH):
    z = D.deck_z(x, y)
    return (
        cq.Workplane("XY")
        .workplane(offset=z - depth)
        .circle(0.5 * dia)
        .extrude(depth + 40.0)
        .translate((x, y, 0.0))
    )


def stanchion_holes() -> cq.Workplane:
    """Hull for rekkepaalene, symmetrisk om senterlinjen."""
    out = None
    d = P.STANCHION_D + CLEAR
    for x in P.STANCHION_X:
        hb = C.deck_half_breadth(x)
        y = hb - P.STANCHION_INSET
        for sign in (1, -1):
            h = _pin_hole(x, sign * y, d)
            out = h if out is None else out.union(h)
    return out


def pulpit_holes() -> cq.Workplane:
    """Hull for pulpit (baug) og pushpit (akter)."""
    out = None
    d = P.STANCHION_D + CLEAR
    for xs in (P.PULPIT_X, P.PUSHPIT_X):
        for x in xs:
            hb = C.deck_half_breadth(x)
            y = max(hb - P.STANCHION_INSET, 60.0)
            for sign in (1, -1):
                h = _pin_hole(x, sign * y, d)
                out = h if out is None else out.union(h)
    return out


def mast_step() -> cq.Workplane:
    """Ovalt hull i ruffen for masten.

    Ovalen staar med den lange aksen for-akter, som paa en virkelig
    mastprofil, og laaser dermed masten mot aa vri seg.
    """
    x = P.MAST_STEP_X
    z = D.coach_roof_z(x)
    return (
        cq.Workplane("XY")
        .workplane(offset=z - P.MAST_SOCKET)
        .ellipse(0.5 * P.MAST_HOLE_X, 0.5 * P.MAST_HOLE_Y)
        .extrude(P.MAST_SOCKET + 1.0 * P.SCALE + 40.0)
        .translate((x, 0.0, 0.0))
    )


def winches() -> cq.Workplane:
    """Vinsjene midt paa cockpitkarmen: en lav sokkel og en trommel med
    kuppel paa toppen, dreid som en virkelig vinsj. Smaa nok til aa staa
    paa karmen uten aa bli skaaret av bronnen."""
    out = None
    x = P.WINCH_X
    z = D.coaming_top_z(x)
    yi, yo = D.cockpit_half_width(x), D.coaming_half_width(x)
    rb = min(0.5 * P.WINCH_BASE_D, 0.5 * (yo - yi) - 2.0)
    rd = min(0.5 * P.WINCH_DRUM_D, rb - 8.0)
    for sign in (1, -1):
        y = sign * 0.5 * (yi + yo)
        base = (
            cq.Workplane("XY").workplane(offset=z - 30.0)
            .center(x, y).circle(rb).extrude(30.0 + 0.16 * P.WINCH_H)
        )
        base = _round_top(base, 0.4 * (0.16 * P.WINCH_H + 30.0))
        drum = (
            cq.Workplane("XY").workplane(offset=z - 10.0)
            .center(x, y).circle(rd).extrude(10.0 + P.WINCH_H)
        )
        drum = _round_top(drum, 0.45 * rd)
        w = base.union(drum)
        out = w if out is None else out.union(w)
    return out



def _round_top(wp: cq.Workplane, r: float) -> cq.Workplane:
    """Fillet paa overkanten av en fri kloss; feiler den, beholdes kanten."""
    try:
        out = wp.faces(">Z").edges().fillet(r)
        if out.val().isValid():
            return out
    except Exception:  # pragma: no cover
        pass
    return wp


def _cleat(x: float, y: float) -> cq.Workplane:
    """Hornklamp langs baaten: en lav fot og to horn med skraa underside
    (printes uten stoette). Sideprofilen er en lukket spline; klampen loftes
    gjennom profilen skalert ned mot sidene, saa alle kanter blir runde uten
    fillet (fillet paa de korte kantene ga hull i STL-en)."""
    L, W, H = P.CLEAT_L, P.CLEAT_W, P.CLEAT_H
    z = min(D.deck_z(x, y - 0.5 * W), D.deck_z(x, y + 0.5 * W))
    a = 0.5 * L
    half = [(0.0, -25.0), (0.18 * L, -25.0), (0.22 * L, -10.0), (0.22 * L, 0.13 * H),
            (0.29 * L, 0.3 * H), (0.39 * L, 0.45 * H), (0.48 * L, 0.6 * H), (a, 0.77 * H),
            (0.49 * L, 0.93 * H), (0.42 * L, H), (0.22 * L, 1.01 * H), (0.0, 1.02 * H)]
    prof = half + [(-px, pz) for (px, pz) in reversed(half[1:-1])]
    r = min(9.0, 0.3 * W)                    # kantradius
    cz, hx, hz = 0.5 * (H - 25.0), a, 0.5 * (H + 25.0)
    e = 0.5 * W - r
    wires = []
    for yy in (-(e + 0.95 * r), -(e + 0.6 * r), -e, 0.0, e, e + 0.6 * r, e + 0.95 * r):
        u = max(0.0, abs(yy) - e)
        s = r - math.sqrt(max(r * r - u * u, 0.0))      # krymp mot sidene
        sx, sz = (hx - s) / hx, (hz - s) / hz
        sp = cq.Edge.makeSpline([cq.Vector(x + px * sx, y + yy, z + cz + (pz - cz) * sz)
                                 for px, pz in prof], periodic=True)
        wires.append(cq.Wire.assembleEdges([sp]))
    return cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=False)])


def cleats() -> cq.Workplane:
    """Fortoyningsklamper: smaa hornklamper, innenfor dekkskanten."""
    out = None
    for x in P.CLEAT_X:
        hb = C.deck_half_breadth(x)
        for sign in (1, -1):
            c = _cleat(x, sign * (hb - P.CLEAT_INSET))
            out = c if out is None else out.union(c)
    return out


def stemhead() -> cq.Workplane:
    """Stevnbeslaget med ankerrullen: et lavt, avrundet beslag som staar paa
    fordekket bak stevnen. Det gaar bare litt ned i dekket og holder seg
    innenfor dekkskanten, saa ingenting stikker ut foran eller under stevnen."""
    x0, x1 = P.STEMHEAD_X
    w = P.STEMHEAD_W
    xs = [x0, 0.5 * (x0 + x1), x1]
    z_lo = min(D.deck_z(x, s * 0.5 * w) for x in xs for s in (0.0, 1.0)) - 15.0
    z_hi = D.deck_z(0.5 * (x0 + x1), 0.0) + P.STEMHEAD_H
    b = (
        cq.Workplane("XY").workplane(offset=z_lo)
        .center(0.5 * (x0 + x1), 0.0)
        .slot2D(x1 - x0, w)
        .extrude(z_hi - z_lo)
    )
    return _round_top(b, 0.3 * w)



def additions() -> cq.Workplane:
    """Alt som skal unioneres inn i skroget."""
    out = winches().union(cleats()).union(stemhead())
    name = transom_name()
    if name is not None:
        out = out.union(name)
    return out


def rudder_pin_holes() -> cq.Workplane:
    """Hull i akterspeilet for rortappene, under vannlinjen der hekken er massiv."""
    from . import appendages as A

    return A.rudder_pins(extra=CLEAR).translate((-0.35 * P.SCALE, 0.0, 0.0))


def cuts() -> cq.Workplane:
    """Alt som skal skjaeres ut av skroget."""
    return (
        stanchion_holes()
        .union(pulpit_holes())
        .union(mast_step())
        .union(rudder_pin_holes())
    )


def transom_name() -> cq.Workplane:
    """Baatens navn i relieff paa akterspeilet.

    Bokstavene ekstruderes fra 40 mm inne i skroget og ut, dreid saa de
    staar vinkelrett paa det hellende akterspeilet, og kappes av akter-
    speilets flate flyttet NAME_RAISE akterover - saa relieffet er like
    hoyt over hele den buede flaten. Sett P.BOAT_NAME til "" for aa droppe det.
    """
    if not P.BOAT_NAME:
        return None
    from . import hull as H

    depth = 40.0
    xc = C.transom_x(P.NAME_Z, 0.0)
    ang = math.degrees(math.atan(P.TRANSOM_RAKE))
    txt = (
        cq.Workplane("YZ")
        .workplane(offset=xc - depth)
        .text(
            P.BOAT_NAME,
            P.NAME_SIZE,
            depth + P.NAME_RAISE + 30.0,
            fontPath="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            halign="center",
            valign="center",
        )
        .translate((0.0, 0.0, P.NAME_Z))
        .rotate((xc, 0.0, P.NAME_Z), (xc, 1.0, P.NAME_Z), ang)
    )
    return txt.cut(H.transom_cutter(offset=P.NAME_RAISE))
