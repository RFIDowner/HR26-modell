"""Kjol og ror."""
from __future__ import annotations

import math

import cadquery as cq
import numpy as np

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


def _offset_foil_wire(x_le: float, z: float, chord: float, thick: float, off: float) -> cq.Wire:
    """Profilet forskjoevet `off` utover langs normalen i snittplanet."""
    pts = np.array(_foil(chord, thick))
    if off > 0.0:
        d = np.roll(pts, -1, axis=0) - np.roll(pts, 1, axis=0)
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        pts = pts + off * np.c_[-d[:, 1], d[:, 0]]      # utover: profilet gaar med klokka
    v = [cq.Vector(x_le + px, py, z) for (px, py) in pts]
    return cq.Wire.assembleEdges([cq.Edge.makeSpline(v + [v[0]])])


def _keel_fillet_offset(d: float) -> float:
    """Kjolens utvidelse mot skroget, d mm under overgangen (negativ: inne i
    skroget). Ved overgangen er den 0,75 x KEEL_FILLET og flaten heller 30
    grader mot bunnen (et tydelig snitt, ikke tangerende, saa unionen er
    robust); KEEL_FILLET lenger ned gaar den tangentielt over i kjolsiden."""
    r = P.KEEL_FILLET
    a = 0.75 * r
    slope = 1.0 / math.tan(math.radians(30.0))
    if d <= 0.0:
        return a + slope * (-d)
    if d >= r:
        return 0.0
    k = slope * r / a
    return a * (1.0 - d / r) ** k


def keel() -> cq.Workplane:
    """Finnekjol, loftet mellom rot og bunn. Stikker opp i skroget for union.

    Mot skroget utvides profilet (KEEL_FILLET), saa overgangen blir en
    hulkil i stedet for en skarp kant. Kanobunnen ligger nesten vannrett
    langs roten (innen ca. 7 mm), saa utvidelsen bygges inn i vannrette
    snitt rundt overgangshoyden - ingen fillet i OCC.
    """
    root_z = C.bottom_z(0.5 * (P.KEEL_LE_ROOT + P.KEEL_TE_ROOT)) + 260.0

    def section(z):
        t = (z - root_z) / (P.KEEL_TIP_Z - root_z)
        le = P.KEEL_LE_ROOT + (P.KEEL_LE_TIP - P.KEEL_LE_ROOT) * (t ** 0.85)
        te = P.KEEL_TE_ROOT + (P.KEEL_TE_TIP - P.KEEL_TE_ROOT) * (t ** 1.30)
        th = P.KEEL_ROOT_T + (P.KEEL_TIP_T - P.KEEL_ROOT_T) * t
        return le, te - le, th

    steps = 7
    zs = [root_z + (P.KEEL_TIP_Z - root_z) * i / steps for i in range(steps + 1)]
    r = P.KEEL_FILLET
    if r <= 0.0:
        wires = [_foil_wire(*_le_z(section(z), z)) for z in zs]
        return cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=False)])

    # overgangen: kanobunnens hoyde der kjolsiden moeter den, midlet langs roten
    le, ch, th = section(zs[1])
    z_j = []
    for x in np.linspace(le + 0.1 * ch, le + 0.9 * ch, 9):
        sec = np.asarray(C.section(float(x), 60), dtype=float)
        z_j.append(float(np.interp(0.5 * th, sec[:, 0], sec[:, 1])))
    zj = float(np.mean(z_j))

    fil = [zj + f * r for f in (0.7, 0.35, 0.0, -0.2, -0.4, -0.6, -0.8, -1.0)]
    wires = [_foil_wire(*_le_z(section(zs[0]), zs[0]))]
    for z in fil:
        le, ch, th = section(z)
        wires.append(_offset_foil_wire(le, z, ch, th, _keel_fillet_offset(zj - z)))
    wires += [_foil_wire(*_le_z(section(z), z)) for z in zs if z < zj - 1.6 * r]
    return cq.Workplane("XY").newObject([_loft3(wires)])


def _le_z(sec, z):
    le, ch, th = sec
    return le, z, ch, th


def _loft3(wires) -> cq.Solid:
    """Glatt loft med hoyst tredjegrads flate paa tvers av snittene (som
    hull._loft3); standardloften svinger mellom tett og glissent plasserte snitt."""
    from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections

    b = BRepOffsetAPI_ThruSections(True, False, 1e-6)
    b.SetMaxDegree(3)
    for w in wires:
        b.AddWire(w.wrapped)
    b.Build()
    return cq.Solid(b.Shape())


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
    """Akterhengt ror. Forkanten foelger akterspeilets helning (RUDDER_RAKE
    er negativ: forover nedover), med RUDDER_GAP klaring til akterspeilet."""
    wires = []
    steps = 5
    for i in range(steps + 1):
        t = i / steps
        z = P.RUDDER_TOP_Z + (P.RUDDER_BOT_Z - P.RUDDER_TOP_Z) * t
        le = P.RUDDER_X + P.RUDDER_RAKE * t
        ch = P.RUDDER_TE_X - le
        th = P.RUDDER_T * (1.0 - 0.28 * t)
        wires.append(_foil_wire(le, z, ch, th))
    solid = cq.Solid.makeLoft(wires, ruled=False)
    return cq.Workplane("XY").newObject([solid]).union(rudder_pins())
