"""Ruff, cockpit med karm, nedgangskapp og luker.

Alle overbygg bygges som loddrette prismer med avrundede hjorner, som
deretter snittes mot et takvolum. Da blir hjorneradiene forutsigbare og
de boolske operasjonene robuste.
"""
from __future__ import annotations

import cadquery as cq

from . import curves as C
from . import params as P

deck_z = C.deck_z


# --------------------------------------------------------------- hjelpere
def _plan_prism(outline, z0: float, z1: float, rad: float) -> cq.Workplane:
    """Loddrett prisme av en planform (liste med (x, y)) med avrundede hjorner."""
    wp = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .polyline(outline)
        .close()
        .extrude(z1 - z0)
    )
    if rad > 0:
        try:
            wp = wp.edges("|Z").fillet(rad)
        except Exception:  # pragma: no cover - radius for stor for kort side
            pass
    return wp


def _roof_body(x0: float, x1: float, top_at, half_w: float, depth: float) -> cq.Workplane:
    """Volum begrenset oppe av en buet takflate, ellers rikelig stort."""
    wires = []
    steps = 10
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        zt0 = top_at(x)
        pts = []
        n = 12
        for j in range(n + 1):
            a = -1.0 + 2.0 * j / n
            pts.append(cq.Vector(x, a * half_w, zt0 - 58.0 * a * a))
        low = [cq.Vector(x, half_w, zt0 - depth), cq.Vector(x, -half_w, zt0 - depth)]
        loop = [low[1]] + pts + [low[0]]
        edges = [
            cq.Edge.makeLine(loop[0], loop[1]),
            cq.Edge.makeSpline(loop[1:-1]),
            cq.Edge.makeLine(loop[-2], loop[-1]),
            cq.Edge.makeLine(loop[-1], loop[0]),
        ]
        wires.append(cq.Wire.assembleEdges(edges))
    return cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=False)])


# ------------------------------------------------------------------- ruff
def coach_half_width(x: float) -> float:
    t = (x - P.COACH_X0) / (P.COACH_X1 - P.COACH_X0)
    t = min(max(t, 0.0), 1.0)
    w = P.COACH_HALF_W0 + (P.COACH_HALF_W1 - P.COACH_HALF_W0) * (t ** 0.70)
    return max(220.0, min(w, C.deck_half_breadth(x) - P.SIDEDECK_MIN))


def _coach_outline(inflate: float = 0.0, n: int = 14):
    xs = [P.COACH_X0 + (P.COACH_X1 - P.COACH_X0) * i / n for i in range(n + 1)]
    stb = [(x, coach_half_width(x) + inflate) for x in xs]
    port = [(x, -(coach_half_width(x) + inflate)) for x in reversed(xs)]
    return stb + port


def coach_roof_z(x: float) -> float:
    t = (x - P.COACH_X0) / (P.COACH_X1 - P.COACH_X0)
    t = min(max(t, 0.0), 1.0)
    return C.sheer_z(x) + P.COACH_H0 + (P.COACH_H1 - P.COACH_H0) * t


def coachroof() -> cq.Workplane:
    """Ruffen: loddrett prisme snittet mot den buede takflaten."""
    z0 = min(C.sheer_z(x) for x in (P.COACH_X0, P.COACH_X1)) - 160.0
    z1 = max(coach_roof_z(x) for x in (P.COACH_X0, P.COACH_X1)) + 60.0
    prism = _plan_prism(_coach_outline(), z0, z1, P.COACH_RAD)
    roof = _roof_body(
        P.COACH_X0 - 400.0,
        P.COACH_X1 + 400.0,
        coach_roof_z,
        P.COACH_HALF_W1 + 600.0,
        2400.0,
    )
    return prism.intersect(roof)


def coach_windows() -> cq.Workplane:
    """Nedfelte langvinduer i ruffsiden."""
    xa, xb = P.COACH_X0 + 560.0, P.COACH_X1 - 300.0
    xm = 0.5 * (xa + xb)
    w = coach_half_width(xm)
    z = C.sheer_z(xm) + 0.55 * (coach_roof_z(xm) - C.sheer_z(xm)) + 40.0
    out = None
    for sign in (1, -1):
        b = (
            cq.Workplane("XY")
            .box(xb - xa, 150.0, 175.0, centered=(True, True, True))
            .edges("|X")
            .fillet(60.0)
            .translate((xm, sign * (w - 20.0), z))
        )
        out = b if out is None else out.union(b)
    return out


# ---------------------------------------------------------------- cockpit
def cockpit_half_width(x: float) -> float:
    t = (x - P.COCKPIT_X0) / (P.COCKPIT_X1 - P.COCKPIT_X0)
    t = min(max(t, 0.0), 1.0)
    w = P.COCKPIT_HALF_W * (1.0 - 0.12 * t)
    return max(200.0, min(w, C.deck_half_breadth(x) - P.SIDEDECK_MIN - 40.0))


def _cockpit_outline(inflate: float = 0.0, n: int = 10):
    xs = [P.COCKPIT_X0 + (P.COCKPIT_X1 - P.COCKPIT_X0) * i / n for i in range(n + 1)]
    stb = [(x, cockpit_half_width(x) + inflate) for x in xs]
    port = [(x, -(cockpit_half_width(x) + inflate)) for x in reversed(xs)]
    return stb + port


def coaming_block() -> cq.Workplane:
    """Opphoyd cockpitkarm. Unioneres for bronnen skjaeres ut."""
    zs = min(C.sheer_z(x) for x in (P.COCKPIT_X0, P.COCKPIT_X1))
    top = max(C.sheer_z(x) for x in (P.COCKPIT_X0, P.COCKPIT_X1)) + P.COAMING_H
    return _plan_prism(_cockpit_outline(95.0), zs - 220.0, top, P.COCKPIT_RAD + 70.0)


def cockpit_cut() -> cq.Workplane:
    """Cockpitbronnen som skjaeres bort."""
    zb = min(C.sheer_z(x) for x in (P.COCKPIT_X0, P.COCKPIT_X1)) - P.COCKPIT_DEPTH
    ztop = max(C.sheer_z(x) for x in (P.COCKPIT_X0, P.COCKPIT_X1)) + P.COAMING_H + 300.0
    return _plan_prism(_cockpit_outline(0.0), zb, ztop, P.COCKPIT_RAD)


def companionway_cut() -> cq.Workplane:
    """Nedgangskapp i ruffens bakkant."""
    x = P.COACH_X1
    z0 = C.sheer_z(x) + 30.0
    return (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .rect(820.0, 640.0)
        .extrude(1100.0)
        .edges("|Z")
        .fillet(80.0)
        .translate((x - 240.0, 0.0, 0.0))
    )


def fore_hatch() -> cq.Workplane:
    """Forluke paa fordekket (grunn utsparing)."""
    x = P.COACH_X0 - 760.0
    return (
        cq.Workplane("XY")
        .workplane(offset=C.deck_z(x, 0.0) - 30.0)
        .rect(540.0, 540.0)
        .extrude(200.0)
        .edges("|Z")
        .fillet(70.0)
        .translate((x, 0.0, 0.0))
    )
