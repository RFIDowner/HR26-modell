"""Ruff, luker, ventiler, nedgang, vindu i skrogsiden, sprayhood og cockpit.

Hoyder og lengder er fra profiltegningen 1:50, bredder fra dekksplanen.
Ruffen er lav og bred paa et flatt fordekk; vinduet sitter i skrogsiden,
i baandet mellom fenderlisten og dekkskanten. Se README under "Merk om
ruffen".

Overbygg bygges som loddrette prismer med avrundede hjorner som snittes
mot et takvolum. Da blir hjorneradiene forutsigbare og de boolske
operasjonene robuste.
"""
from __future__ import annotations

import math

import cadquery as cq

from . import curves as C
from . import params as P
from . import shell as S

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
    """Ruffens halvbredde i plan: dekkshalvbredden minus sidedekket,
    med rundet front fra STEP_X0 og COACH_FRONT_R akterover."""
    w = max(P.COACH_MIN_HALF_W, C.deck_half_breadth(x) - P.SIDEDECK)
    R = P.COACH_FRONT_R
    if x < P.STEP_X0 + R:
        u = (P.STEP_X0 + R - x) / R
        w *= math.sqrt(max(0.0, 1.0 - u * u))
    return w


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


def _plan_prism_outline(stb, z0: float, z1: float, aft_rad: float = 0.0) -> cq.Workplane:
    """Loddrett prisme av en speilsymmetrisk planform gitt av styrbord-
    punktene `stb` (fra forkant til akterkant, foerste punkt paa senter-
    linjen). Sidene er splines, akterkanten rett, akterhjornene rundet
    med `aft_rad`. Ingen fillet etterpaa - de kan feile stille paa korte
    segmenter."""
    xa, wa = stb[-1]
    r = min(aft_rad, 0.45 * wa)
    c = math.sqrt(0.5)
    wp = cq.Workplane("XY").workplane(offset=z0).moveTo(*stb[0])
    side = list(stb[1:])
    if r > 0:
        side[-1] = (xa - r, wa)
    wp = wp.spline(side, includeCurrent=True)
    if r > 0:
        wp = wp.threePointArc((xa - r + r * c, wa - r + r * c), (xa, wa - r))
        wp = wp.lineTo(xa, -(wa - r))
        wp = wp.threePointArc((xa - r + r * c, -(wa - r + r * c)), (xa - r, -wa))
    else:
        wp = wp.lineTo(xa, -wa)
    port = [(x, -y) for (x, y) in reversed(side[:-1])] + [stb[0]]
    wp = wp.spline(port, includeCurrent=True)
    return wp.close().extrude(z1 - z0)


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


# ------------------------------------------------------------------- ruff
def _step_wedge() -> cq.Workplane:
    """Volumet foran/over ruffens skraa front - fjernes fra ruffen.

    Fronten gaar fra dekket ved STEP_X0 opp til taket ved STEP_X1."""
    za = deck_z(P.STEP_X0, 0.0) - 35.0
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
    """Ruffen: lav og bred, rundet front, skraa front opp til taket."""
    z0 = min(C.sheer_z(x) for x in (P.STEP_X0, P.COACH_X1)) - 200.0
    z1 = max(z for _, z in P.COACH_TOP) + 80.0
    n = 60
    stb = [(P.STEP_X0 + (P.COACH_X1 - P.STEP_X0) * i / n, 0.0) for i in range(n + 1)]
    stb = [(x, coach_half_width(x)) for x, _ in stb]
    prism = _plan_prism_outline(stb, z0, z1, P.COACH_RAD)
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
    """Soppventiler: en paa fordekket, en paa taket bak masten."""
    out = None
    for x, where in P.VENTS:
        base = (deck_z(x, 0.0) if where == "deck" else roof_z(x)) - 40.0
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
    z0 = deck_z(x, 0.0) + P.COMPANION_SILL
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


def _window_box(grow: float) -> cq.Workplane:
    """Vinduets omriss sett fra siden, ekstrudert tvers gjennom baaten.

    Underkanten foelger fenderlisten, overkanten dekkskanten, slik tegningen
    viser. `grow` gjor omrisset stoerre paa alle kanter."""
    x0, x1 = P.WIN_X0 - grow, P.WIN_X1 + grow
    lo = lambda x: C.strake_z(x) + P.WIN_ABOVE_STRAKE - grow
    hi = lambda x: C.sheer_z(x) - P.WIN_BELOW_DECK + grow
    pts = [(x0, lo(x0)), (x1, lo(x1)), (x1, hi(x1)), (x0, hi(x0))]
    b = cq.Workplane("XZ").polyline(pts).close().extrude(3000.0, both=True)
    try:
        b = b.edges("|Y").fillet(P.WIN_RAD + grow)
    except Exception:  # pragma: no cover
        pass
    return b


def _inside_loft(depth: float, x0: float, x1: float, n: int = 8) -> cq.Workplane:
    """Skrogets innside forskjoevet `depth` innover, loftet mellom x0 og x1."""
    xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]
    wires = [S._inner_wire(x, depth, 0.0) for x in xs]
    return cq.Workplane("XY").newObject([cq.Solid.makeLoft(wires, ruled=True)])


def hull_windows():
    """Langvinduene i skrogsiden: (kutt, behold).

    Kuttet er et WIN_DEPTH tykt baand langs begge skrogsider innenfor
    vinduets omriss. `behold` er et tykkere baand bak vinduet som gis til
    uthulingen, saa det staar full veggtykkelse igjen bak forsenkningen."""
    xa, xb = P.WIN_X0 - 200.0, P.WIN_X1 + 200.0
    cut = _window_box(0.0).cut(_inside_loft(P.WIN_DEPTH, xa, xb))
    keep_depth = P.WIN_DEPTH + P.HULL_WALL + P.VOID_MARGIN + 10.0
    keep = _window_box(100.0).cut(_inside_loft(keep_depth, xa - 100.0, xb + 100.0))
    return cut, keep


def mast_post() -> cq.Workplane:
    """Massiv soyle under mastesteget, fra bunnen opp til taket, med en
    kloss rundt sokkelen. Gis til uthulingen som `keep`: ellers ville
    sokkelen (330 mm ned fra taket) aapnet seg inn i hulrommet."""
    x = P.MAST_STEP_X
    z0 = C.bottom_z(x) + 20.0
    z1 = roof_z(x) + 10.0
    post = (
        cq.Workplane("XY").workplane(offset=z0).center(x, 0.0)
        .rect(P.MAST_POST_W, P.MAST_POST_W).extrude(z1 - z0)
    )
    zb = roof_z(x) - P.MAST_SOCKET - 60.0
    block = (
        cq.Workplane("XY").workplane(offset=zb).center(x, 0.0)
        .rect(260.0, 230.0).extrude(z1 - zb)
    )
    return post.union(block)


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
        # ruffens bredde foran nedgangen, karmens bredde over cockpiten
        t_w = min(max((x - P.COACH_X1) / 300.0, 0.0), 1.0)
        w = (1.0 - t_w) * coach_half_width(min(x, P.COACH_X1)) + t_w * coaming_half_width(x)
        w += P.SPRAY_OVERHANG
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
    return max(200.0, min(P.COCKPIT_HALF_W, C.deck_half_breadth(x) - 290.0))


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


def cockpit_floor_z() -> float:
    """Bronnens gulv over DWL."""
    return P.COCKPIT_FLOOR_Z


def _cockpit_lid_z(x: float) -> float:
    """Hvor hoyt bronnen skjaeres: til karmtoppen under sprayhooden, saa
    sprayhoodens utheng blir staaende, og hoyere aktenfor den, saa dekkets
    bue ikke legger en hinne over bronnen."""
    t = min(max((x - P.SPRAY_X1 - 50.0) / 200.0, 0.0), 1.0)
    return coaming_top_z(x) + 12.0 + 200.0 * t


def cockpit_tub(grow: float) -> cq.Workplane:
    """Bronnen vokst med `grow` paa alle kanter: karet som omslutter den.

    Med grow = skallveggen er dette gulvet og veggene rundt bronnen. Det
    gis til uthulingen som `keep`, saa bronnen faar bunn og sider.
    """
    def hw(x):
        return cockpit_half_width(x) + grow

    z1 = max(coaming_top_z(x) for x in (P.COCKPIT_X0, P.COCKPIT_X1)) + 200.0
    return _plan_prism(
        _outline(P.COCKPIT_X0 - grow, P.COCKPIT_X1 + grow, hw),
        cockpit_floor_z() - grow, z1, P.COCKPIT_RAD + grow,
    )


def cockpit_cut() -> cq.Workplane:
    """Cockpitbronnen. Skjaeres bare opp til karmtoppen, saa sprayhoodens utheng blir staaende."""
    z0 = cockpit_floor_z()
    prism = _plan_prism(_outline(P.COCKPIT_X0, P.COCKPIT_X1, cockpit_half_width), z0, 2600.0, P.COCKPIT_RAD)
    top = _roof_body(P.COCKPIT_X0 - 300.0, P.COCKPIT_X1 + 300.0, _cockpit_lid_z, 1500.0, 2600.0, camber=0.0)
    return prism.intersect(top)
