"""Avtakbart ruff-tak (lokk) og aapningen ned i kahytten.

Ruffen med luker, takventil og sprayhood blir en egen del, 16_ruff-tak.
Skjoeten ligger LID_LIFT over dekket og foelger dekket rundt hele ruffens
fot, saa den blir en jevn, smal linje. Under skjoeten blir en lav krage av
ruffsiden staaende paa skroget, og innenfor den en tynn kant (LIP_*) som
lokket tres ned over, saa det sitter fast og paa plass. Lokket er hult
(LID_WALL) og aapent nedover; innenfor kanten er dekket aapent ned i
kahytten.

Lokket printes med taket opp. Skjoeten foelger dekket og er ikke plan,
saa lokket trenger litt stoette under kanten, og stoette inni under taket.

Alt i fullskala-mm i byggekoordinater, som resten av modellen.
"""
from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from . import curves as C
from . import deckhouse as D
from . import params as P


# ------------------------------------------------------------- omriss
def _outline():
    """Ruffens fot i plan (styrbord halvdel), som i deckhouse."""
    return D._coach_planform()


def _beta(f):
    """Sidens vinkel fra vannrett (radianer) for et punkt som vender
    forover med andelen f (som i deckhouse._hf_section)."""
    a0, a1 = P.COACH_FRONT_ANGLE, P.COACH_SIDE_ANGLE
    return np.radians(a1 + (a0 - a1) * f * f)


def inset_planform(t_normal: float, extra: float = 0.0) -> D._Planform:
    """Omrisset forskjoevet innover saa en vegg med normaltykkelse
    t_normal faar riktig tykkelse i den hellende siden, pluss `extra`
    vannrett. Forenden flyttes akterover, sidene innover og akterkanten
    forover. Punktene holder voksende x."""
    pl = _outline()
    p, nv = pl.p, pl.nv
    f = np.clip(-nv[:, 0], 0.0, 1.0)
    d = t_normal / np.sin(_beta(f)) + extra
    q = p - d[:, None] * nv
    q[0, 1] = 0.0                       # spissen paa senterlinjen
    # akterkanten (siste punkt) flyttes forover like mye som veggen
    q[-1, 0] = p[-1, 0] - (t_normal / math.sin(math.radians(P.COACH_SIDE_ANGLE)) + extra)
    keep = [0]
    for i in range(1, len(q)):
        if q[i, 0] > q[keep[-1], 0] + 1e-6 and q[i, 1] >= 0.0:
            keep.append(i)
    return D._Planform(q[keep])


# ------------------------------------------------------- skjoeteflaten
def above_split(lift: float | None = None, x0: float = 2000.0, x1: float = 6300.0,
                half: float = 1600.0, z_top: float = 2400.0, step: float = 100.0) -> cq.Workplane:
    """Alt over flaten deck_z + lift mellom x0 og x1 (et volum som loftes
    gjennom tverrsnitt). Utenfor dekkets halvbredde fortsetter flaten flatt
    ut til siden."""
    lift = P.LID_LIFT if lift is None else lift
    xs = np.arange(x0, x1 + 0.5 * step, step)
    ny = 41
    wires = []
    for x in xs:
        hb = C.deck_half_breadth(float(x))
        ys = np.linspace(-hb, hb, ny)
        zs = [C.deck_z(float(x), float(y)) + lift for y in ys]
        pts = [cq.Vector(float(x), -half, zs[0])]
        pts += [cq.Vector(float(x), float(y), float(z)) for y, z in zip(ys, zs)]
        pts += [cq.Vector(float(x), half, zs[-1])]
        bottom = cq.Edge.makeSpline(pts[1:-1], parameters=list(np.linspace(0.0, 1.0, ny)))
        e = [cq.Edge.makeLine(pts[0], pts[1]), bottom, cq.Edge.makeLine(pts[-2], pts[-1]),
             cq.Edge.makeLine(pts[-1], cq.Vector(float(x), half, z_top)),
             cq.Edge.makeLine(cq.Vector(float(x), half, z_top), cq.Vector(float(x), -half, z_top)),
             cq.Edge.makeLine(cq.Vector(float(x), -half, z_top), pts[0])]
        wires.append(cq.Wire.assembleEdges(e))
    solid = cq.Solid.makeLoft(wires, ruled=False)
    if not solid.isValid():
        raise RuntimeError("skjoeteflaten ga et ugyldig volum")
    return cq.Workplane("XY").newObject([solid])


# ------------------------------------------------------------- lokket
def lid_raw() -> cq.Workplane:
    """Det som hoerer til lokket foer det kappes: ruffen, lukene,
    takventilen og sprayhooden."""
    out = D.coachroof()
    out = out.union(D.hatches())
    for x, where in P.VENTS:
        if where == "roof":
            base = D.roof_z(x) - 40.0
            v = (cq.Workplane("XY").workplane(offset=base).center(x, 0.0)
                 .circle(0.5 * P.VENT_D).extrude(40.0 + P.VENT_H))
            try:
                v = v.faces(">Z").edges().fillet(0.4 * P.VENT_D)
            except Exception:  # pragma: no cover
                pass
            out = out.union(v)
    out = out.union(D.sprayhood())
    return out


def lid_hollow() -> cq.Workplane:
    """Hulrommet i lokket: et hoydefelt over omrisset forskjoevet innover
    LID_WALL, med taket LID_WALL lavere. Gaar ned under skjoeten, saa
    lokket blir aapent nedover."""
    plan = inset_planform(P.LID_WALL)
    xs = [x for x in D._coach_stations() if plan.p[0, 0] + 2.0 < x < plan.p[-1, 0] - 2.0]
    xs = [plan.p[0, 0] + 4.0] + xs + [plan.p[-1, 0] - 1.0]
    rf = max(P.COACH_FRONT_EDGE_R - P.LID_WALL, 15.0)
    rs = max(P.COACH_EDGE_R - P.LID_WALL, 15.0)
    return D._hf_solid(
        xs, plan,
        base=lambda x, y: C.deck_z(x, y) - 120.0,
        top=lambda x, y: D.roof_surface_z(x, y) - P.LID_WALL,
        floor=lambda x, y: C.deck_z(x, y) - 200.0,
        angles=(P.COACH_FRONT_ANGLE, P.COACH_SIDE_ANGLE),
        radii=(rf, rs),
        what="hulrom i lokket",
    )


def mast_hole() -> cq.Workplane:
    """Hull for masten gjennom taket (masten limes)."""
    x = P.MAST_STEP_X
    z = D.roof_z(x)
    return (cq.Workplane("XY").workplane(offset=z - 400.0).center(x, 0.0)
            .ellipse(0.5 * P.MAST_HOLE_X, 0.5 * P.MAST_HOLE_Y).extrude(600.0))


def lid(split: cq.Workplane | None = None) -> cq.Workplane:
    """Ruff-taket som egen del, i byggekoordinater."""
    split = above_split() if split is None else split
    w = lid_raw().intersect(split)
    w = w.cut(lid_hollow())
    w = w.cut(D.companionway_cut())
    w = w.cut(mast_hole())
    return w


# --------------------------------------------------- kant paa skroget
def _stations_for(plan: D._Planform):
    xs = [x for x in D._coach_stations() if plan.p[0, 0] + 2.0 < x < plan.p[-1, 0] - 2.0]
    return [plan.p[0, 0] + 4.0] + xs + [plan.p[-1, 0] - 1.0]


def _ring(plan_out: D._Planform, plan_in: D._Planform, z_lo, z_hi) -> cq.Workplane:
    """Ring mellom to omriss, fra z_lo(x, y) til z_hi(x, y)."""
    def solid(plan):
        return D._hf_solid(
            _stations_for(plan), plan, base=z_lo, top=z_hi,
            floor=lambda x, y: z_lo(x, y) - 40.0,
            angles=(89.0, 89.0), radii=(2.0, 2.0), what="kant")
    return solid(plan_out).cut(solid(plan_in))


def lip() -> cq.Workplane:
    """Kanten paa skroget som lokket tres ned over."""
    t_h = P.LID_WALL
    out = inset_planform(t_h, extra=P.LID_CLEAR)
    inn = inset_planform(t_h, extra=P.LID_CLEAR + P.LIP_W)
    lo = lambda x, y: C.deck_z(x, y) + P.LID_LIFT - 15.0
    hi = lambda x, y: C.deck_z(x, y) + P.LID_LIFT + P.LIP_H
    ring = _ring(out, inn, lo, hi)
    return ring.cut(D.companionway_cut())


def deck_opening(z_bottom: float = -400.0) -> cq.Workplane:
    """Aapningen gjennom dekket og kragen innenfor kanten, ned til z_bottom
    (kahyttens hulrom tar over der)."""
    inn = inset_planform(P.LID_WALL, extra=P.LID_CLEAR + P.LIP_W)
    return D._hf_solid(
        _stations_for(inn), inn,
        base=lambda x, y: z_bottom,
        top=lambda x, y: C.deck_z(x, y) + P.LID_LIFT + P.LIP_H + 200.0,
        floor=lambda x, y: z_bottom - 50.0,
        angles=(89.5, 89.5), radii=(2.0, 2.0), what="aapning i dekket",
    )
