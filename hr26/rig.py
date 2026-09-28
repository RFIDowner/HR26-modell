"""Riggen som byggesett.

Masten er et ovalt emne, 4,0 x 3,0 mm i modellen, som kappes til lengde.
En alu-mastprofil er dypere for-akter enn paa tvers, og den ovale formen
laaser samtidig masten mot aa vri seg i beslagene - derfor er alle hull i
riggdelene ovale, ikke runde.

Alt annet printes: mastefot, salingbeslag, masttopp, bom, og en boyemal
for pulpit og pushpit av 1,5 mm messingtraad.

Delene modelleres i fullskala som resten, og skaleres ned i build.py.
"""
from __future__ import annotations

import math

import cadquery as cq

from . import deckhouse as D
from . import params as P

HX, HY = P.MAST_HOLE_X, P.MAST_HOLE_Y            # hullet, 4,5 x 3,5 mm
SX, SY = P.MAST_SECTION_X, P.MAST_SECTION_Y      # masten, 4,0 x 3,0 mm


def _try(fn, fallback):
    """Kjorer en avrunding, men lar delen staa om OCC ikke finner kanter."""
    try:
        return fn()
    except Exception:
        return fallback


def _oval(wp, ax: float, ay: float):
    """Ellipse med akser ax (for-akter) og ay (tvers) - ikke radier."""
    return wp.ellipse(0.5 * ax, 0.5 * ay)


def mast_length_model_mm() -> float:
    """Anbefalt lengde paa masteemnet, i modell-mm."""
    return (P.MAST_ABOVE_WL - D.coach_roof_z(P.MAST_STEP_X)) / P.SCALE


def boom_length_model_mm() -> float:
    return P.BOOM_LEN / P.SCALE


def mast_foot() -> cq.Workplane:
    """Mastefot: lavt, stopt beslag paa ruffen som masten staar nedi.

    HR 26 har dekksmontert mast, og foten er et synlig beslag paa ruffen -
    derfor er den med, men holdt lav og platelignende slik originalen er.
    """
    plate_h = 1.1 * P.SCALE
    boss_h = 3.4 * P.SCALE
    plate = _oval(cq.Workplane("XY"), HX + 5.2 * P.SCALE, HY + 4.6 * P.SCALE).extrude(
        plate_h
    )
    boss = (
        _oval(
            cq.Workplane("XY").workplane(offset=plate_h),
            HX + 2.4 * P.SCALE,
            HY + 2.2 * P.SCALE,
        )
        .extrude(boss_h)
    )
    body = plate.union(boss)
    body = _try(lambda: body.faces(">Z").edges().fillet(0.5 * P.SCALE), body)
    return _oval(
        body.faces(">Z").workplane(), HX, HY
    ).cutThruAll()


def masthead() -> cq.Workplane:
    """Masttopp med hull for forstag og akterstag."""
    h = 5.5 * P.SCALE
    body = _oval(cq.Workplane("XY"), HX + 2.2 * P.SCALE, HY + 2.0 * P.SCALE).extrude(h)
    body = _oval(
        body.faces(">Z").workplane(), HX, HY
    ).cutBlind(-(h - 1.4 * P.SCALE))
    d = 0.5 * P.SCALE
    span = HX + 6.0 * P.SCALE
    for ang in (0.0, 180.0):
        body = body.cut(
            cq.Workplane("XZ")
            .workplane(offset=-0.5 * span)
            .circle(0.5 * d)
            .extrude(span)
            .rotate((0, 0, 0), (0, 0, 1), ang)
            .translate((0, 0, h * 0.58))
        )
    return body


def spreaders() -> cq.Workplane:
    """Salingbeslag med tilbakesveipte armer.

    Det ovale navet gjor at armene ikke kan snurre rundt masten.
    """
    hub_h = 3.0 * P.SCALE
    hub = _oval(cq.Workplane("XY"), HX + 2.4 * P.SCALE, HY + 2.2 * P.SCALE).extrude(
        hub_h
    )
    L = P.SPREADER_LEN
    out = hub
    for sign in (1, -1):
        arm = (
            cq.Workplane("XZ")
            .rect(1.4 * P.SCALE, 1.1 * P.SCALE)
            .extrude(L)
            .rotate((0, 0, 0), (0, 0, 1), 90 * sign)
            .rotate((0, 0, 0), (0, 0, 1), -sign * P.SPREADER_SWEEP)
        )
        out = out.union(arm.translate((0, 0, 0.5 * hub_h)))
    return _oval(out.faces(">Z").workplane(), HX, HY).cutThruAll()


def boom() -> cq.Workplane:
    """Bom med ring som tres om masten."""
    L = P.BOOM_LEN
    b0 = cq.Workplane("YZ").rect(1.9 * P.SCALE, 1.5 * P.SCALE).extrude(L)
    b = _try(lambda: b0.edges("|X").fillet(0.35 * P.SCALE), b0)
    ring_h = 2.4 * P.SCALE
    ring = _oval(
        cq.Workplane("XY").workplane(offset=-0.5 * ring_h),
        HX + 2.2 * P.SCALE,
        HY + 2.0 * P.SCALE,
    ).extrude(ring_h)
    ring = _oval(ring.faces(">Z").workplane(), HX, HY).cutThruAll()
    return b.union(ring)


def wire_jig() -> cq.Workplane:
    """Boyemal for pulpit og pushpit av 1,5 mm messingtraad."""
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
