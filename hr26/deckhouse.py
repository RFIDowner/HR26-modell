"""Ruff i to nivaaer, luker, ventiler, nedgang, sprayhood og cockpit.

Alt er bygget fra maalingene i data/deckhouse_features.json: hoyder og
lengder fra profiltegningen 1:50, bredder fra scannet (midtskips) og foto
(forover). Se README under "Merk om ruffen".

Overbygg bygges som loddrette prismer med avrundede hjorner som snittes
mot et takvolum. Da blir hjorneradiene forutsigbare og de boolske
operasjonene robuste.
"""
from __future__ import annotations

import cadquery as cq

from . import curves as C
from . import params as P

deck_z = C.deck_z


# ---------------------------------------------------------------- kurver
def _interp(table, x: float) -> float:
    xs = [t[0] for t in table]
    ys = [t[1] for t in table]
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return ys[-1]


def roof_z(x: float) -> float:
    """Den hoye ruffens topp paa senterlinjen."""
    return _interp(P.COACH_TOP, min(max(x, P.COACH_X0), P.COACH_X1))


coach_roof_z = roof_z   # eldre navn, brukes av fittings og rig


def coach_half_width(x: float) -> float:
    """Den hoye ruffens halvbredde i plan."""
    w = _interp(P.COACH_HALF_W, min(max(x, P.STEP_X0), P.COACH_X1))
    return max(220.0, min(w, C.deck_half_breadth(x) - P.SIDEDECK_MIN))


def trunk_half_width(x: float) -> float:
    """Den lave forruffens halvbredde."""
    hb = C.deck_half_breadth(x)
    return max(120.0, min(P.TRUNK_W_FRAC * hb, hb - 180.0))


def coach_side_span(x: float):
    """Ruffsidens fot og takkant ved stasjon x: (z_fot, z_topp)."""
    w = coach_half_width(x)
    return deck_z(x, w), roof_z(x) - P.COACH_ROOF_CAMBER


def coaming_top_z(x: float) -> float:
    """Cockpitkarmens overkant over DWL."""
    t = (x - P.COCKPIT_X0) / (P.COCKPIT_X1 - P.COCKPIT_X0)
    t = min(max(t, 0.0), 1.0)
    return C.sheer_z(x) + P.COAMING_H0 + (P.COAMING_H1 - P.COAMING_H0) * t


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


def _outline(x0: float, x1: float, hw, n: int = 16):
    xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
    stb = [(x, hw(x)) for x in xs]
    port = [(x, -hw(x)) for x in reversed(xs)]
    return stb + port


def _roof_body(x0, x1, top_at, half_w: float, depth: float, camber: float) -> cq.Workplane:
    """Volum begrenset oppe av en (eventuelt buet) takflate, ellers rikelig stort."""
    wires = []
    steps = 12
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        zt = top_at(x)
        pts = []
        n = 12
        for j in range(n + 1):
            a = -1.0 + 2.0 * j / n
            pts.append(cq.Vector(x, a * half_w, zt - camber * a * a))
        low = [cq.Vector(x, half_w, zt - depth), cq.Vector(x, -half_w, zt - depth)]
        loop = [low[1]] + pts + [low[0]]
        edges = [
            cq.Edge.makeLine(loop[0], loop[1]),
            cq.Edge.makeSpline(loop[1:-1]) if camber else cq.Edge.makeLine(loop[1], loop[-2]),
            cq.Edge.makeLine(loop[-2], loop[-1]),
            cq.Edge.makeLine(loop[-1], loop[0]),
        ]
        wires.append(cq.Wire.assembleEdges(edges))
    return cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=False)])


def _rounded_block(x0, x1, w, z0, z1, rad, top_chamfer=0.0) -> cq.Workplane:
    b = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .center(0.5 * (x0 + x1), 0.0)
        .rect(x1 - x0, w)
        .extrude(z1 - z0)
    )
    try:
        b = b.edges("|Z").fillet(min(rad, 0.45 * min(x1 - x0, w)))
    except Exception:  # pragma: no cover
        pass
    if top_chamfer > 0:
        try:
            b = b.faces(">Z").chamfer(top_chamfer)
        except Exception:  # pragma: no cover
            pass
    return b


# ------------------------------------------------------------- forruff
def trunk() -> cq.Workplane:
    """Lav, flat forruff fra trinnet og fram til den fairer inn i fordekket."""
    z0 = min(C.sheer_z(x) for x in (P.TRUNK_X0, P.STEP_X1)) - 200.0
    prism = _plan_prism(_outline(P.TRUNK_X0, P.STEP_X1 + 60.0, trunk_half_width),
                        z0, P.TRUNK_TOP_Z + 60.0, P.TRUNK_RAD)
    roof = _roof_body(P.TRUNK_X0 - 300.0, P.STEP_X1 + 400.0, lambda x: P.TRUNK_TOP_Z,
                      1400.0, 2200.0, camber=22.0)
    return prism.intersect(roof)


# ------------------------------------------------------------------- ruff
def _step_wedge() -> cq.Workplane:
    """Volumet foran/over trinnets skraa front - fjernes fra den hoye ruffen."""
    za = P.TRUNK_TOP_Z
    zb = roof_z(P.STEP_X1) + 5.0
    pts = [
        (P.STEP_X0, za - 5.0),
        (P.STEP_X1, zb),
        (P.STEP_X1, zb + 2500.0),
        (P.STEP_X0 - 600.0, zb + 2500.0),
        (P.STEP_X0 - 600.0, za - 5.0),
    ]
    return cq.Workplane("XZ").polyline(pts).close().extrude(2500.0, both=True)


def coachroof() -> cq.Workplane:
    """Den hoye ruffen med skraatt trinn forut."""
    z0 = min(C.sheer_z(x) for x in (P.STEP_X0, P.COACH_X1)) - 200.0
    z1 = max(z for _, z in P.COACH_TOP) + 80.0
    prism = _plan_prism(_outline(P.STEP_X0, P.COACH_X1, coach_half_width), z0, z1, P.COACH_RAD)
    roof = _roof_body(P.STEP_X0 - 300.0, P.COACH_X1 + 300.0, roof_z, 1500.0, 2400.0,
                      camber=P.COACH_ROOF_CAMBER)
    return prism.intersect(roof).cut(_step_wedge())


def hatches() -> cq.Workplane:
    """Forluke foran masten og skyveluke over nedgangen, begge paa taket."""
    out = None
    for (x0, x1, w, h) in (P.FOREHATCH, P.SLIDE_HATCH):
        xm = 0.5 * (x0 + x1)
        zb = roof_z(xm) - P.COACH_ROOF_CAMBER - 20.0
        zt = roof_z(xm) + h
        b = _rounded_block(x0, x1, w, zb, zt, 70.0, top_chamfer=15.0)
        out = b if out is None else out.union(b)
    return out


def vents() -> cq.Workplane:
    """Soppventiler: en paa forruffen, en paa taket bak masten."""
    out = None
    for x, where in P.VENTS:
        base = (P.TRUNK_TOP_Z if where == "trunk" else roof_z(x)) - 40.0
        v = (
            cq.Workplane("XY")
            .workplane(offset=base)
            .center(x, 0.0)
            .circle(0.5 * P.VENT_D)
            .extrude(40.0 + P.VENT_H)
        )
        try:
            v = v.faces(">Z").edges().fillet(0.4 * P.VENT_D)
        except Exception:  # pragma: no cover
            pass
        out = v if out is None else out.union(v)
    return out


def companionway_cut() -> cq.Workplane:
    """Nedgangen: fordypning i ruffens bakkant."""
    x = P.COACH_X1
    z0 = C.sheer_z(x) + P.COMPANION_SILL
    z1 = roof_z(x) + 150.0
    b = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .center(x + 100.0 - 0.5 * P.COMPANION_DEPTH, 0.0)
        .rect(P.COMPANION_DEPTH + 200.0, P.COMPANION_W)
        .extrude(z1 - z0)
    )
    try:
        b = b.edges("|X").fillet(60.0)
    except Exception:  # pragma: no cover
        pass
    return b


def coach_windows() -> cq.Workplane:
    """Nedfelte langvinduer i ruffsiden, i nedre halvdel av siden."""
    L = P.COACH_X1 - P.COACH_X0
    xa = P.COACH_X0 + P.WIN_X0_FRAC * L
    xb = P.COACH_X0 + P.WIN_X1_FRAC * L
    xm = 0.5 * (xa + xb)
    z_bot, z_top = coach_side_span(xm)
    H = z_top - z_bot
    z0 = z_bot + P.WIN_Z0_FRAC * H
    z1 = z_bot + P.WIN_Z1_FRAC * H
    w = coach_half_width(xm)
    out = None
    for sign in (1, -1):
        b = (
            cq.Workplane("XY")
            .box(xb - xa, P.WIN_DEPTH, z1 - z0, centered=(True, True, True))
            .edges("|Y")
            .fillet(min(P.WIN_RAD, 0.45 * (z1 - z0)))
            .translate((xm, sign * (w - 0.5 * P.WIN_DEPTH + 40.0), 0.5 * (z0 + z1)))
        )
        out = b if out is None else out.union(b)
    return out


# ------------------------------------------------------------- sprayhood
def sprayhood() -> cq.Workplane:
    """Sprayhood over nedgangen, henger ut over cockpiten.

    Modellert massiv - i 1:30 ville veggene i en aapen kalesje blitt under
    en halv millimeter. Frontvindu males heller inn.
    """
    x0, x1 = P.SPRAY_X0, P.SPRAY_X1
    wires = []
    steps = 10
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        w = coach_half_width(min(x, P.COACH_X1)) + P.SPRAY_OVERHANG
        base = (roof_z(x) if x <= P.COACH_X1 else coaming_top_z(x)) - 70.0
        top = P.SPRAY_TOP_Z - 45.0 * (1.0 - t)
        pts = []
        n = 12
        for j in range(n + 1):
            a = -1.0 + 2.0 * j / n
            pts.append(cq.Vector(x, a * w, base + (top - base) * (1.0 - abs(a) ** 3.2)))
        wires.append(cq.Wire.assembleEdges([cq.Edge.makeSpline(pts), cq.Edge.makeLine(pts[-1], pts[0])]))
    return cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=False)])


# --------------------------------------------------------------- cockpit
def cockpit_half_width(x: float) -> float:
    return max(200.0, min(P.COCKPIT_HALF_W, C.deck_half_breadth(x) - P.SIDEDECK_MIN - 40.0))


def coaming_half_width(x: float) -> float:
    return max(260.0, min(P.COAMING_HALF_W, C.deck_half_breadth(x) - 200.0))


def coaming_block() -> cq.Workplane:
    """Cockpitkarm med skraa overkant. Unioneres for bronnen skjaeres ut."""
    z0 = min(C.sheer_z(x) for x in (P.COCKPIT_X0, P.COCKPIT_X1)) - 220.0
    z1 = max(coaming_top_z(x) for x in (P.COCKPIT_X0, P.COCKPIT_X1)) + 60.0
    prism = _plan_prism(_outline(P.COCKPIT_X0 - 40.0, P.COCKPIT_X1, coaming_half_width),
                        z0, z1, P.COCKPIT_RAD + 60.0)
    top = _roof_body(P.COCKPIT_X0 - 300.0, P.COCKPIT_X1 + 300.0, coaming_top_z, 1500.0, 2000.0, camber=0.0)
    return prism.intersect(top)


def cockpit_cut() -> cq.Workplane:
    """Cockpitbronnen. Skjaeres bare opp til karmtoppen, saa sprayhoodens utheng blir staaende."""
    z0 = min(C.sheer_z(x) for x in (P.COCKPIT_X0, P.COCKPIT_X1)) - P.COCKPIT_DEPTH
    prism = _plan_prism(_outline(P.COCKPIT_X0, P.COCKPIT_X1, cockpit_half_width), z0, 2600.0, P.COCKPIT_RAD)
    top = _roof_body(P.COCKPIT_X0 - 300.0, P.COCKPIT_X1 + 300.0,
                     lambda x: coaming_top_z(x) + 12.0, 1500.0, 2600.0, camber=0.0)
    return prism.intersect(top)
