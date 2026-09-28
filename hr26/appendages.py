"""Kjol og ror."""
from __future__ import annotations

import math

import cadquery as cq

from . import curves as C
from . import params as P


def _foil(chord: float, thick: float, n: int = 22, te: float | None = None):
    """Symmetrisk NACA-lignende profil med butt bakkant.

    En knivskarp bakkant er baade uprintbar og en kilde til ugyldige
    flater i lofting og avrunding, saa bakkanten gis en liten tykkelse.
    """
    t = thick / chord
    te = (0.55 * P.SCALE) if te is None else te      # 0,55 mm i modellen
    te_half = 0.5 * min(te, 0.35 * thick) / chord
    up, lo = [], []
    for i in range(n + 1):
        beta = math.pi * i / n
        xc = 0.5 * (1.0 - math.cos(beta))          # fortetning i for- og bakkant
        yt = (
            5.0
            * t
            * (
                0.2969 * math.sqrt(xc)
                - 0.1260 * xc
                - 0.3516 * xc ** 2
                + 0.2843 * xc ** 3
                - 0.1015 * xc ** 4
            )
        )
        yt += te_half * xc
        up.append((xc * chord, yt * chord))
        lo.append((xc * chord, -yt * chord))
    pts = up + list(reversed(lo[1:]))
    return pts


def _foil_wire(x_le: float, z: float, chord: float, thick: float) -> cq.Wire:
    pts = _foil(chord, thick)
    v = [cq.Vector(x_le + px, py, z) for (px, py) in pts]
    return cq.Wire.assembleEdges(
        [cq.Edge.makeSpline(v + [v[0]])]
    )


def keel() -> cq.Workplane:
    """Finnekjol, loftet mellom rot og bunn. Stikker opp i skroget for union."""
    root_z = C.bottom_z(0.5 * (P.KEEL_LE_ROOT + P.KEEL_TE_ROOT)) + 260.0
    wires = []
    steps = 7
    for i in range(steps + 1):
        t = i / steps
        le = P.KEEL_LE_ROOT + (P.KEEL_LE_TIP - P.KEEL_LE_ROOT) * (t ** 0.85)
        te = P.KEEL_TE_ROOT + (P.KEEL_TE_TIP - P.KEEL_TE_ROOT) * (t ** 1.30)
        z = root_z + (P.KEEL_TIP_Z - root_z) * t
        th = P.KEEL_ROOT_T + (P.KEEL_TIP_T - P.KEEL_ROOT_T) * t
        wires.append(_foil_wire(le, z, te - le, th))
    solid = cq.Solid.makeLoft(wires, ruled=False)
    return cq.Workplane("XY").newObject([solid])


def _pin_positions():
    for z in P.RUDDER_PIN_Z:
        t = (z - P.RUDDER_TOP_Z) / (P.RUDDER_BOT_Z - P.RUDDER_TOP_Z)
        yield P.RUDDER_X + P.RUDDER_RAKE * t, z


def rudder_pins(extra: float = 0.0) -> cq.Workplane:
    """Tappene paa rorets forkant (og malen for hullene i akterspeilet)."""
    out = None
    d = P.RUDDER_PIN_D + extra
    for x, z in _pin_positions():
        c = (
            cq.Workplane("YZ")
            .workplane(offset=x - P.RUDDER_PIN_L)
            .circle(0.5 * d)
            .extrude(P.RUDDER_PIN_L + 0.3 * P.SCALE)
            .translate((0, 0, z))
        )
        out = c if out is None else out.union(c)
    return out


def rudder() -> cq.Workplane:
    """Akterhengt ror med rorkult-tapp."""
    wires = []
    steps = 5
    for i in range(steps + 1):
        t = i / steps
        z = P.RUDDER_TOP_Z + (P.RUDDER_BOT_Z - P.RUDDER_TOP_Z) * t
        le = P.RUDDER_X + P.RUDDER_RAKE * t
        ch = P.RUDDER_CHORD_TOP + (P.RUDDER_CHORD_BOT - P.RUDDER_CHORD_TOP) * t
        th = P.RUDDER_T * (1.0 - 0.28 * t)
        wires.append(_foil_wire(le, z, ch, th))
    solid = cq.Solid.makeLoft(wires, ruled=False)
    return cq.Workplane("XY").newObject([solid]).union(rudder_pins())
