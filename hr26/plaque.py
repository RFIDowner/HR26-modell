"""Skiltplate til modellen.

En liten plate med opphoyd tekst som forteller hva modellen er: baatens
navn, konstruktor, byggeaar, hovedmaal og maalestokk. Ment aa staa foran
eller ved siden av stativet.

I motsetning til resten av pakken modelleres platen direkte i MODELL-
millimeter, siden den ikke er en nedskalering av noe paa baaten. Den
skaleres derfor opp med SCALE her, slik at build.py kan behandle den som
alle andre deler.
"""
from __future__ import annotations

import cadquery as cq

from . import params as P

FONT = "DejaVu Sans"

# plate i modell-mm
W = 104.0
H = 46.0
T = 3.0
EDGE = 2.2
RAISE = 0.7          # tekstens hoyde over platen

NAME = P.BOAT_NAME                       # baatens navn, under typen
TYPE_LINE = "Hallberg-Rassy 26"          # typen staar oeverst, storst
TYPE_SIZE = 9.0                          # 10,5 mm ville vaert for bredt for platen
NAME_SIZE = 7.0
# De smaa linjene staar i fet skrift, 6 mm: strekene blir ca. 1 mm brede og
# lesbare uten at man maa se noeye etter. Vanlig skrift paa 3,1 mm ga strek paa
# ca. 0,3 mm, som slicere dropper, og 4,2 mm ble for smaatt paa platen.
LINE_SIZE = 6.0
LINES = [
    "Konstrukt\u00f8r Olle Enderlein",
    "Ell\u00f6s, Sverige  \u00b7  1978\u201385",
]
SCALE_LINE = "Skala 1:30"


def _text(s: str, size: float, y: float, bold: bool = False) -> cq.Workplane:
    """Tekstlinje midtstilt paa platen: bredden maales paa selve bokstavene,
    saa linjen ligger midt paa uansett hva fonten legger til av luft."""
    t = (
        cq.Workplane("XY")
        .workplane(offset=T)
        .text(
            s,
            size,
            RAISE,
            fontPath="/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
            % ("-Bold" if bold else ""),
            halign="center",
            valign="center",
        )
    )
    bb = t.val().BoundingBox()
    return t.translate((-0.5 * (bb.xmin + bb.xmax), y, 0.0))


def plaque_model_mm() -> cq.Workplane:
    """Platen i modell-millimeter."""
    plate = (
        cq.Workplane("XY")
        .rect(W, H)
        .extrude(T)
        .edges("|Z")
        .fillet(3.0)
    )
    plate = plate.faces(">Z").edges().chamfer(0.6)

    # innfelt ramme som gir plata litt liv
    plate = plate.cut(
        cq.Workplane("XY")
        .workplane(offset=T - 0.4)
        .rect(W - 2 * EDGE, H - 2 * EDGE)
        .extrude(1.0)
        .cut(
            cq.Workplane("XY")
            .workplane(offset=T - 0.4)
            .rect(W - 2 * EDGE - 1.2, H - 2 * EDGE - 1.2)
            .extrude(1.0)
        )
    )

    body = plate
    if NAME:
        body = body.union(_text(TYPE_LINE, TYPE_SIZE, 14.9, bold=True))
        body = body.union(_text(NAME, NAME_SIZE, 6.9, bold=True))
    else:
        body = body.union(_text(TYPE_LINE.upper(), 6.4, 10.0, bold=True))
    for i, line in enumerate(LINES):
        body = body.union(_text(line, LINE_SIZE, -0.2 - i * 7.9, bold=True))
    body = body.union(_text(SCALE_LINE, LINE_SIZE, -16.0, bold=True))
    return body


def plaque() -> cq.Workplane:
    """Platen skalert opp til byggekoordinater, slik resten av pakken er."""
    wp = plaque_model_mm()
    return cq.Workplane("XY").newObject([wp.val().scale(P.SCALE)])


def parts() -> dict:
    return {"skilt": plaque()}
