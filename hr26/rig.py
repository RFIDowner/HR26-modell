"""Riggen som byggesett.

Masten er en 4 mm trepinne eller karbonroer som kappes til lengde. Alt
annet printes: mastefot, salingbeslag, masttopp, bom med lekter, og en
boyemal for pulpit og pushpit av 1,5 mm messingtraad.

Delene modelleres i fullskala som resten, og skaleres ned i build.py.
"""
from __future__ import annotations

import math

import cadquery as cq

from . import deckhouse as D
from . import params as P

CORE = P.MAST_CORE_D            # 4 mm i modellen
FIT = 0.12 * P.SCALE            # passklaring


def _try(fn, fallback):
    """Kjorer en avrunding, men lar delen staa om OCC ikke finner kanter."""
    try:
        return fn()
    except Exception:
        return fallback


def mast_length_model_mm() -> float:
    """Anbefalt lengde paa mastepinnen, i modell-mm."""
    top = P.MAST_ABOVE_WL
    foot = D.coach_roof_z(P.MAST_STEP_X)
    return (top - foot) / P.SCALE


def boom_length_model_mm() -> float:
    return P.BOOM_LEN / P.SCALE


def mast_foot() -> cq.Workplane:
    """Mastefot: sokkel som limes i ruffen, med hylse for kjernen."""
    h = 9.0 * P.SCALE
    return (
        cq.Workplane("XY")
        .circle(0.5 * CORE + 1.3 * P.SCALE)
        .extrude(h)
        .faces(">Z")
        .workplane()
        .circle(0.5 * (CORE + FIT))
        .cutBlind(-(h - 1.6 * P.SCALE))
    )


def masthead() -> cq.Workplane:
    """Masttopp med hull for forstag, akterstag og fall."""
    h = 6.0 * P.SCALE
    body = (
        cq.Workplane("XY")
        .circle(0.5 * CORE + 1.1 * P.SCALE)
        .extrude(h)
        .faces(">Z")
        .workplane()
        .circle(0.5 * (CORE + FIT))
        .cutBlind(-(h - 1.4 * P.SCALE))
    )
    d = 0.5 * P.SCALE
    for ang in (0.0, 180.0):
        r = 0.5 * CORE + 0.9 * P.SCALE
        body = body.cut(
            cq.Workplane("XZ")
            .workplane(offset=-r - 1.0)
            .circle(0.5 * d)
            .extrude(2 * r + 2.0)
            .rotate((0, 0, 0), (0, 0, 1), ang)
            .translate((0, 0, h * 0.55))
        )
    return body


def spreaders() -> cq.Workplane:
    """Salingbeslag med tilbakesveipte armer."""
    hub_h = 3.2 * P.SCALE
    hub = (
        cq.Workplane("XY")
        .circle(0.5 * CORE + 1.2 * P.SCALE)
        .extrude(hub_h)
        .faces(">Z")
        .workplane()
        .circle(0.5 * (CORE + FIT))
        .cutThruAll()
    )
    a = math.radians(P.SPREADER_SWEEP)
    L = P.SPREADER_LEN
    out = hub
    for sign in (1, -1):
        arm = (
            cq.Workplane("XZ")
            .workplane(offset=0.0)
            .moveTo(0, 0)
            .rect(1.4 * P.SCALE, 1.1 * P.SCALE)
            .extrude(L)
            .rotate((0, 0, 0), (0, 0, 1), 90 * sign)
        )
        arm = arm.rotate((0, 0, 0), (0, 0, 1), -sign * P.SPREADER_SWEEP)
        out = out.union(arm.translate((0, 0, 0.5 * hub_h)))
    return out


def boom() -> cq.Workplane:
    """Bom med gaffel som klemmer om masten."""
    L = P.BOOM_LEN
    b0 = cq.Workplane("YZ").rect(1.9 * P.SCALE, 1.5 * P.SCALE).extrude(L)
    b = _try(lambda: b0.edges("|X").fillet(0.35 * P.SCALE), b0)
    ring = (
        cq.Workplane("XY")
        .circle(0.5 * CORE + 1.1 * P.SCALE)
        .extrude(2.4 * P.SCALE)
        .faces(">Z")
        .workplane()
        .circle(0.5 * (CORE + FIT))
        .cutThruAll()
        .translate((0, 0, -1.2 * P.SCALE))
    )
    return b.union(ring)


def wire_jig() -> cq.Workplane:
    """Boyemal for pulpit og pushpit av 1,5 mm messingtraad.

    Platen har tapper som traaden boyes rundt, og mal-hull som viser
    hvor beina skal staa i dekket.
    """
    t = 3.0 * P.SCALE
    w = 34.0 * P.SCALE
    l = 46.0 * P.SCALE
    plate = cq.Workplane("XY").box(l, w, t, centered=(True, True, False))
    peg_r = 0.5 * (P.STANCHION_D + 0.6 * P.SCALE)
    pegs = [
        (-15.0, 0.0),
        (-6.0, 9.0),
        (-6.0, -9.0),
        (6.0, 12.0),
        (6.0, -12.0),
        (16.0, 11.0),
        (16.0, -11.0),
    ]
    for px, py in pegs:
        plate = plate.union(
            cq.Workplane("XY")
            .workplane(offset=t)
            .circle(peg_r)
            .extrude(6.0 * P.SCALE)
            .translate((px * P.SCALE, py * P.SCALE, 0.0))
        )
    return plate


def parts() -> dict:
    return {
        "mastefot": mast_foot(),
        "masttopp": masthead(),
        "saling": spreaders(),
        "bom": boom(),
        "boyemal": wire_jig(),
    }
