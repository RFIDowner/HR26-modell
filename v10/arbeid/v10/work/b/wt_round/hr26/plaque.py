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
# Liberation Sans Bold (Arial-lik) er ca. 15 % smalere enn DejaVu Sans Bold,
# saa samme bredde gir stoerre bokstaver. DejaVu hadde et oeye i "e" paa bare
# 0,7 mm2 og tynne haler paa "y", og de fylles igjen/forsvinner i sliceren.
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
TYPE_SIZE = 10.0
NAME_SIZE = 7.5
LINE_SIZE = 6.8                          # strek ca. 1,1 mm - lesbart og printbart
BLOCK_HALF_H = 18.6                      # tekstblokken ligger mellom +-18,6 mm
LINES = [
    "Konstrukt\u00f8r Olle Enderlein",
    "Ell\u00f6s, Sverige  \u00b7  1978\u201385",
]
SCALE_LINE = "Skala 1:30"


def _text(s: str, size: float):
    """Tekstlinje midtstilt i x og y paa selve bokstavene (ikke fontens luft).
    Gir (linje, blekkhoeyde) med linjen i origo paa platens overflate."""
    t = (
        cq.Workplane("XY")
        .workplane(offset=T)
        .text(s, size, RAISE, fontPath=FONT_BOLD, halign="center", valign="center")
    )
    bb = t.val().BoundingBox()
    return (
        t.translate((-0.5 * (bb.xmin + bb.xmax), -0.5 * (bb.ymin + bb.ymax), 0.0)),
        bb.ylen,
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

    items = []
    if NAME:
        items.append(_text(TYPE_LINE, TYPE_SIZE))
        items.append(_text(NAME, NAME_SIZE))
    else:
        items.append(_text(TYPE_LINE.upper(), TYPE_SIZE))
    items += [_text(line, LINE_SIZE) for line in LINES]
    items.append(_text(SCALE_LINE, LINE_SIZE))

    # like stor luft mellom alle linjer, blokken symmetrisk om platens midte
    total = sum(h for _, h in items)
    gap = (2.0 * BLOCK_HALF_H - total) / (len(items) - 1)
    body = plate
    y = BLOCK_HALF_H
    for line, h in items:
        body = body.union(line.translate((0.0, y - 0.5 * h, 0.0)))
        y -= h + gap
    return body


def plaque() -> cq.Workplane:
    """Platen skalert opp til byggekoordinater, slik resten av pakken er."""
    wp = plaque_model_mm()
    return cq.Workplane("XY").newObject([wp.val().scale(P.SCALE)])


def parts() -> dict:
    return {"skilt": plaque()}
