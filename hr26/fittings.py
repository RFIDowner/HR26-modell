"""Utsparinger i dekket: mastefot, rekkepaaler, pulpit, pushpit, vinsjer.

Alle hull er dimensjonert for 1,5 mm messingtraad (P.STANCHION_D) med litt
klaring, slik at traaden sitter stramt uten aa sprenge dekket.
"""
from __future__ import annotations

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
    """Utsparing i ruffen for mastefoten: senterhull for kjernen."""
    x = P.MAST_STEP_X
    z = D.coach_roof_z(x)
    return (
        cq.Workplane("XY")
        .workplane(offset=z - 11.0 * P.SCALE)
        .circle(0.5 * (P.MAST_CORE_D + CLEAR))
        .extrude(12.0 * P.SCALE + 40.0)
        .translate((x, 0.0, 0.0))
    )


def winch_pads() -> cq.Workplane:
    """Sokler for selvhalende vinsjer paa cockpitkarmen."""
    out = None
    for sign in (1, -1):
        y = sign * (C.deck_half_breadth(P.WINCH_X) - P.WINCH_INSET)
        z = D.deck_z(P.WINCH_X, y)
        pad = (
            cq.Workplane("XY")
            .workplane(offset=z - 260.0)
            .circle(150.0)
            .extrude(450.0)
            .faces(">Z")
            .chamfer(35.0)
            .translate((P.WINCH_X, y, 0.0))
        )
        out = pad if out is None else out.union(pad)
    return out


def cleats() -> cq.Workplane:
    """Fortoyningsklamper: enkle klosser, gode nok i 1:30."""
    out = None
    for x in P.CLEAT_X:
        hb = C.deck_half_breadth(x)
        for sign in (1, -1):
            y = sign * (hb - 150.0)
            z = D.deck_z(x, y)
            c = (
                cq.Workplane("XY")
                .workplane(offset=z - 280.0)
                .rect(260.0, 90.0)
                .extrude(380.0)
                .edges("|Z")
                .fillet(40.0)
                .translate((x, y, 0.0))
            )
            out = c if out is None else out.union(c)
    return out


def anchor_roller() -> cq.Workplane:
    """Stevnbeslag med ankerrulle paa fordekket."""
    x = 430.0
    z = D.deck_z(x, 0.0)
    return (
        cq.Workplane("XY")
        .workplane(offset=z - 420.0)
        .rect(520.0, 170.0)
        .extrude(560.0)
        .edges("|Z")
        .fillet(60.0)
        .translate((x, 0.0, 0.0))
    )


def additions() -> cq.Workplane:
    """Alt som skal unioneres inn i skroget."""
    out = winch_pads().union(cleats()).union(anchor_roller())
    return out


def rudder_pin_holes() -> cq.Workplane:
    """Hull i akterspeilet for rortappene."""
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
