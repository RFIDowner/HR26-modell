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
H = 34.0
T = 3.0
EDGE = 2.2
RAISE = 0.7          # tekstens hoyde over platen

TITLE = "HALLBERG-RASSY 26"
LINES = [
    "Konstrukt\u00f8r Olle Enderlein  ·  bygget 1978–1985",
    "Lengde 7,95 m  ·  Bredde 2,68 m  ·  Dypgang 1,40 m",
    "Deplasement 2,5 t  ·  Seilareal 32 m²",
]
SCALE_LINE = "Skala 1:30"


def _text(s: str, size: float, y: float, bold: bool = False) -> cq.Workplane:
    return (
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
        .translate((0.0, y, 0.0))
    )


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
    body = body.union(_text(TITLE, 6.4, 10.4, bold=True))
    for i, line in enumerate(LINES):
        body = body.union(_text(line, 3.1, 3.0 - i * 4.4))
    body = body.union(_text(SCALE_LINE, 4.0, -12.6, bold=True))
    return body


def plaque() -> cq.Workplane:
    """Platen skalert opp til byggekoordinater, slik resten av pakken er."""
    wp = plaque_model_mm()
    return cq.Workplane("XY").newObject([wp.val().scale(P.SCALE)])


def parts() -> dict:
    return {"skilt": plaque()}
