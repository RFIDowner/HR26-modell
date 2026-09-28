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
        "bom-med-seil": boom_with_sail(),
        "rekkepaaler": stanchions(),
        "boyemal": wire_jig(),
    }


def furled_sail() -> cq.Workplane:
    """Surret storseil med kalesje, slik baaten ligger fortoyd.

    Limes oppa bommen. Vil du ha bar bom, er det bare aa la vaere aa
    printe denne delen.
    """
    L = P.BOOM_LEN - P.SAIL_START
    wires = []
    steps = 8
    for i in range(steps + 1):
        t = i / steps
        x = P.SAIL_START + L * t
        d = P.SAIL_D0 + (P.SAIL_D1 - P.SAIL_D0) * (t ** 0.85)
        if i == steps:
            d *= 0.55                      # nokken smalner av
        wires.append(
            cq.Workplane("YZ")
            .workplane(offset=x)
            .ellipse(0.5 * d, 0.5 * d * 0.86)
            .val()
        )
    solid = cq.Solid.makeLoft(wires, ruled=False)
    sail = cq.Workplane("XY").newObject([solid])
    # antydede surringer rundt seilet
    for k in range(1, 5):
        x = P.SAIL_START + L * k / 5.0
        t = (x - P.SAIL_START) / L
        d = P.SAIL_D0 + (P.SAIL_D1 - P.SAIL_D0) * (t ** 0.85)
        sail = sail.cut(
            cq.Workplane("YZ")
            .workplane(offset=x - 0.10 * P.SCALE)
            .ellipse(0.5 * d + 30.0, 0.5 * d * 0.86 + 30.0)
            .extrude(0.20 * P.SCALE)
            .cut(
                cq.Workplane("YZ")
                .workplane(offset=x - 0.15 * P.SCALE)
                .ellipse(0.5 * d - 0.35 * P.SCALE, 0.5 * d * 0.86 - 0.35 * P.SCALE)
                .extrude(0.30 * P.SCALE)
            )
        )
    return sail


def boom_with_sail() -> cq.Workplane:
    """Bom med surret storseil paa - alternativ til den bare bommen.

    Print enten denne eller `bom`, ikke begge.
    """
    return boom().union(furled_sail().translate((0.0, 0.0, 0.30 * P.SCALE)))


def stanchions() -> cq.Workplane:
    """Ark med rekkepaaler som har ekte oyer for livlinene.

    Hvert oye har et gjennomgaaende hull paa 0,5 mm som tauverket tres
    gjennom. Hullaksen ligger langs X, og delen printes liggende (rotert
    90 grader om Y i build.py) - da staar hullene loddrett og kommer rene
    ut, og lagene loper langs paalen, som er den sterke retningen.
    """
    n = len(P.STANCHION_X) * 2 + P.STANCHION_SPARES
    pitch = 3.4 * P.SCALE
    sprue_t = 0.9 * P.SCALE
    sprue_w = 2.0 * P.SCALE

    out = None
    for i in range(n):
        y = (i - (n - 1) / 2.0) * pitch
        part = (
            cq.Workplane("XY")
            .circle(0.5 * P.STANCHION_SHAFT)
            .extrude(P.STANCHION_H)
            .union(
                cq.Workplane("XY")
                .circle(0.5 * P.STANCHION_SHAFT * 0.92)
                .extrude(-P.STANCHION_PIN)
            )
        )
        for z in P.LIFELINE_Z:
            part = part.union(
                cq.Workplane("XY")
                .workplane(offset=z - 0.5 * P.LIFELINE_EYE_H)
                .rect(P.LIFELINE_EYE_L, P.LIFELINE_EYE_W)
                .extrude(P.LIFELINE_EYE_H)
            )
            part = part.cut(
                cq.Workplane("YZ")
                .workplane(offset=-P.LIFELINE_EYE_L)
                .circle(0.5 * P.LIFELINE_EYE_D)
                .extrude(2.0 * P.LIFELINE_EYE_L)
                .translate((0.0, 0.0, z))
            )
        out = part.translate((0.0, y, 0.0)) if out is None else out.union(
            part.translate((0.0, y, 0.0))
        )

    # sprua ligger under tappene, saa oyene staar fritt og paalene kan
    # klippes av uten aa korte inn tappen mer enn noen tideler
    sprue_top = -P.STANCHION_PIN
    sprue = (
        cq.Workplane("XY")
        .workplane(offset=sprue_top - sprue_w)
        .box(sprue_t, n * pitch, sprue_w, centered=(True, True, False))
    )
    return out.union(sprue)
