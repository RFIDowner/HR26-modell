"""Avtakbart ruff-tak (lokk), kragen og kanten paa skroget.

Ruffen med luker, takventil og sprayhood blir en egen del, 16_ruff-tak.

* Skjoeten er et PLAN (split_z), svakt skraatt for-akter, som staar minst
  LID_LIFT over dekket rundt hele ruffens og sprayhoodens fot. Et plan gjoer
  at lokket kan printes staaende paa skjoeteflaten, rett paa platen og uten
  support. (Et plan som foelger dekket ga en buet underside: 3,5 mm i
  hoyde over lokkets lengde, som maatte staatt paa support.) Skjoeten staar
  1,0 mm over dekket i endene og ca. 2,1 mm midt paa (planet er rett, springen
  er buet).
* Under planet blir en lav krage av ruff og sprayhood staaende paa skroget
  (collar). Paa kragen staar en loddrett kant (lip), og i lokkets underside
  er det et spor (groove) som kanten gaar inn i, med LID_CLEAR klaring paa
  hver side. Kanten gaar rundt fronten og langs sidene, men ikke over
  akterkanten: der er nedgangen, og fronten og sidene holder lokket paa plass
  i alle retninger.
* Lokket er massivt i CAD og printes med glissent fyll (som innredningen).
  Et hult lokk med 2 mm vegg haadde trengt support under hele taket (ca. 70 mm
  spenn, og lokket er bare 6-8 mm hoyt, for lavt for hvelv eller 45 graders
  tak), og masten haadde bare staatt i 2 mm tak.
* Under sprayhooden, aktenfor ruffen, er lokket hult over karmen og bronnen
  (cove): taket der stiger 45 grader fra karmens forkant og innover fra
  sprayhoodens bein, saa det printes uten support og ser ut som det aapne
  kalesjetaket paa baaten (IMG_9372). Nedgangen gaar gjennom lokket ned i
  kahytten.
* Masten staar i et hull gjennom lokket (5-6 mm grep) og ned i et hull i
  mastestoetten (interior._post). Hullet i stoetten er stopp naar masten
  limes i lokket: masten foelger lokket naar det loeftes av. Det gjelder
  masten med sokkel (365 mm, for lang for A1); A1-masten uten sokkel (354
  mm) naar ikke stoetten og staar i mastefoten paa taket.
* Paa skroget aapnes nedgangen ned i kahytten (companion_slot), fra
  aapningens akterkant til foran karmen; ellers ser man bare kragen
  (terskelen) gjennom nedgangen i lokket.

Aapningen i dekket (opening_planform) er innsiden av kanten; interior.py
bruker den.

Alt i fullskala-mm i byggekoordinater, som resten av modellen.
"""
from __future__ import annotations

import functools
import math

import cadquery as cq
import numpy as np

from . import curves as C
from . import deckhouse as D
from . import params as P

X_REF = 4000.0        # planet: z = a + b * (x - X_REF)
W_MIN = 2.0           # minste halve bredde i et tverrsnitt (unngaar null-kanter)
GROOVE_SHORT = []     # (x, gods) der sporet ikke fikk LID_WALL gods (tom naa)


# ------------------------------------------------------------- omriss
def _outline() -> D._Planform:
    """Ruffens fot i plan (styrbord halvdel), som i deckhouse."""
    return D._coach_planform()


def _angles(f):
    """Sidens vinkel fra vannrett (radianer) og takkantens radius for
    punkter som vender forover med andelen f (som i deckhouse._hf_section)."""
    f2 = np.asarray(f) ** 2
    beta = np.radians(P.COACH_SIDE_ANGLE + (P.COACH_FRONT_ANGLE - P.COACH_SIDE_ANGLE) * f2)
    rad = P.COACH_EDGE_R + (P.COACH_FRONT_EDGE_R - P.COACH_EDGE_R) * f2
    return beta, rad


def _stations_for(plan: D._Planform):
    xs = [x for x in D._coach_stations() if plan.p[0, 0] + 2.0 < x < plan.p[-1, 0] - 2.0]
    return [plan.p[0, 0] + 4.0] + xs + [plan.p[-1, 0] - 1.0]


# ------------------------------------------------------- skjoeteplanet
def _spray_deck_half_w(x: float) -> float:
    """Sprayhoodens bein aktenfor ruffen: halv bredde der siden moeter dekket."""
    zf = D._spray_foot_z(x)
    hw = D._spray_half_w(x)
    return hw + (zf - C.deck_z(x, hw)) / math.tan(math.radians(P.SPRAY_SIDE_ANGLE))


@functools.lru_cache(maxsize=None)
def split_plane():
    """(a, b): skjoeten er planet z = a + b * (x - X_REF).

    Planet skal staa minst LID_LIFT over dekket overalt der lokkets underside
    ligger: rundt ruffens fot og 250 mm innover (dekksbuen loefter dekket
    innover), og under sprayhoodens bein paa sidedekket aktenfor ruffen.
    Blant slike plan velges det som staar lavest over dekket ved foten."""
    pl = _outline()
    foot, ring = [], []
    for (x, y), n in zip(pl.p, pl.nv):
        foot.append((x, C.deck_z(x, y)))
        for d in np.linspace(0.0, 250.0, 11):
            xx, yy = x - d * n[0], max(y - d * n[1], 0.0)
            ring.append((xx, C.deck_z(xx, yy)))
    for x in np.arange(P.COACH_X1, P.SPRAY_X1 + 25.0, 25.0):
        for y in np.linspace(D.coaming_half_width(x), _spray_deck_half_w(x), 6):
            foot.append((x, C.deck_z(x, y)))
            ring.append((x, C.deck_z(x, y)))
    F, R = np.array(foot), np.array(ring)
    best = None
    for b in np.linspace(-0.08, 0.02, 2001):
        a = float(np.max(R[:, 1] + P.LID_LIFT - b * (R[:, 0] - X_REF)))
        t = float(np.max(a + b * (F[:, 0] - X_REF) - F[:, 1]))
        if best is None or t < best[0]:
            best = (t, a, float(b))
    return best[1], best[2]


def split_z(x: float) -> float:
    a, b = split_plane()
    return a + b * (x - X_REF)


def print_tilt_deg() -> float:
    """Dreiing om Y (grader) som legger skjoeteplanet vannrett paa platen."""
    return math.degrees(math.atan(split_plane()[1]))


def above_split(x0: float = 2000.0, x1: float = 6300.0, half: float = 1600.0,
                z_top: float = 2400.0) -> cq.Workplane:
    """Alt over skjoeteplanet mellom x0 og x1 (plane flater)."""
    pts = [(x0, split_z(x0)), (x1, split_z(x1)), (x1, z_top), (x0, z_top)]
    return cq.Workplane("XZ").polyline(pts).close().extrude(half, both=True)


# ------------------------------------------------- sporet og kanten (plan)
def _coach_surface_z(xs, ys):
    """Ruffens ytterflate (som deckhouse.coachroof) i punktene (xs, ys)."""
    pl = _outline()
    q = np.c_[xs, np.abs(ys)]
    aq = q[:, None, :] - pl.a[None, :, :]
    t = np.clip(np.einsum("kij,ij->ki", aq, pl.ab) / pl.L2[None, :], 0.0, 1.0)
    diff = aq - t[:, :, None] * pl.ab[None, :, :]
    dd = np.einsum("kij,kij->ki", diff, diff)
    i = np.argmin(dd, axis=1)
    k = np.arange(len(q))
    d = np.sqrt(dd[k, i])
    ti = t[k, i]
    n = (1.0 - ti)[:, None] * pl.nv[i] + ti[:, None] * pl.nv[i + 1]
    n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    inside = np.array([abs(y) < pl.half_width(x) for x, y in zip(xs, ys)])
    d = np.where(inside, d, -d)
    beta, rad = _angles(np.clip(-n[:, 0], 0.0, 1.0))
    zb = np.array([C.deck_z(x, y) for x, y in zip(xs, ys)])
    H = np.array([D.roof_surface_z(x, y) for x, y in zip(xs, ys)]) - zb
    return zb + D._edge_profile(d, H, beta, rad)


@functools.lru_cache(maxsize=None)
def _groove_inset():
    """For hvert punkt paa ruffens fot: hvor langt (vannrett, langs omrissets
    normal) sporets ytterside staar innenfor foten. Sporets oevre ytre hjorne
    (LIP_H + LID_CLEAR_TOP over planet) skal ligge minst LID_WALL innenfor
    ruffens flate, ogsaa i takkantens runding over den lave fronten. Der det
    ikke er plass (spissen av fronten) velges stedet med mest gods."""
    pl = _outline()
    ss = np.linspace(-60.0, 500.0, 561)            # langs normalen, 1 mm
    cand = np.linspace(0.0, 500.0, 501)
    out = np.empty(len(pl.p))
    GROOVE_SHORT.clear()
    for i, ((x, y), nv) in enumerate(zip(pl.p, pl.nv)):
        qx, qy = x - ss * nv[0], y - ss * nv[1]
        zs = _coach_surface_z(qx, qy)
        hg = split_z(x) + P.LIP_H + P.LID_CLEAR_TOP
        dist = np.min(np.hypot(cand[:, None] - ss[None, :], hg - zs[None, :]), axis=1)
        under = hg < np.interp(cand, ss, zs)
        ok = np.nonzero((dist >= P.LID_WALL) & under)[0]
        if len(ok):
            out[i] = cand[ok[0]]
        else:
            j = int(np.argmax(np.where(under, dist, -1.0)))
            out[i] = cand[j]
            GROOVE_SHORT.append((float(x), float(dist[j])))
    return out


def _monotone(q) -> D._Planform:
    """Punktene med voksende x (og y >= 0) som omriss."""
    keep = [0]
    for i in range(1, len(q)):
        if q[i, 0] > q[keep[-1], 0] + 1e-6 and q[i, 1] >= 0.0:
            keep.append(i)
    return D._Planform(q[keep])


@functools.lru_cache(maxsize=None)
def _contour(extra: float) -> D._Planform:
    """Sporets ytterside (extra = 0), eller den flyttet `extra` lenger inn
    langs sin egen normal, saa sporet, kanten og aapningen er parallelle."""
    if extra == 0.0:
        pl = _outline()
        d = _groove_inset()
        q = pl.p - d[:, None] * pl.nv
        q[0, 1] = 0.0                       # spissen paa senterlinjen
        q[-1, 0] = pl.p[-1, 0] - d[-1]      # akterkanten forover
        return _monotone(q)
    g = _contour(0.0)
    q = g.p - extra * g.nv
    q[0, 1] = 0.0
    q[-1, 0] = g.p[-1, 0] - extra
    return _monotone(q)


def groove_planforms():
    """(ytterside, innerside) av sporet i lokkets underside."""
    return _contour(0.0), _contour(2.0 * P.LID_CLEAR + P.LIP_W)


def lip_planforms():
    """(ytterside, innerside) av kanten paa skroget."""
    return _contour(P.LID_CLEAR), _contour(P.LID_CLEAR + P.LIP_W)


def opening_planform() -> D._Planform:
    """Aapningen i dekket: innenfor kanten."""
    return _contour(P.LID_CLEAR + P.LIP_W)


def _prism_stations(pl: D._Planform, x_end: float):
    """Tverrsnitt for et loddrett prisme over omrisset: omrissets egne
    punkter rundt den rundede spissen (de forreste 300 mm), ruffens
    stasjoner videre akterover, og endene."""
    xf = float(pl.p[0, 0])
    # Omrissets egne punkter (spissen og knekkpunkter over 3 grader) gaar
    # foran ruffens stasjoner. Ellers kan en stasjon 0,4 mm fra hjoernet
    # kaste hjoernepunktet, og det rette stykket skjaerer hjoernet av paa
    # sporet men ikke paa kanten (0,045 mm klaring i 1:30, kontroll 13.11).
    d = np.diff(pl.p, axis=0)
    ang = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    turn = np.r_[0.0, np.abs(np.diff(ang)), 0.0]
    own = sorted({xf, x_end} | {float(x) for x, t in zip(pl.p[:, 0], turn)
                                if xf < x < x_end and (x < xf + 300.0 or t > 3.0)})
    kept = [own[0]]
    for x in own[1:]:
        if x - kept[-1] > 3.0:
            kept.append(x)
    kept[-1] = x_end
    xs = sorted(set(kept) | {x for x in D._coach_stations()
                             if xf < x < x_end and min(abs(x - k) for k in kept) > 3.0})
    return xs


def _plan_prism(pl: D._Planform, z0: float, z1: float, x_max: float | None = None,
                ) -> cq.Workplane:
    """Omrisset `pl` (begge sider) fra planet + z0 til planet + z1, loftet med
    rette flater. Ender ved x_max (rett tverrskott) hvis gitt."""
    xa = float(pl.p[-1, 0]) - 1e-3
    x_end = xa if x_max is None else min(x_max, xa)
    wires = []
    for x in _prism_stations(pl, x_end):
        w = max(pl.half_width(x), W_MIN)
        zs = split_z(x)
        pts = [(-w, zs + z0), (w, zs + z0), (w, zs + z1), (-w, zs + z1)]
        wires.append(cq.Wire.makePolygon([cq.Vector(x, y, z) for y, z in pts], close=True))
    solid = cq.Solid.makeLoft(wires, ruled=True)
    if not solid.isValid():
        raise RuntimeError("prisme over omrisset ga et ugyldig volum")
    return cq.Workplane("XY").newObject([solid])


def lip() -> cq.Workplane:
    """Kanten paa skroget som lokket tres ned over: LIP_W tykk, LIP_H over
    skjoeten, og 30 mm ned i kragen. Rundt fronten og langs sidene til
    LIP_X1. To prismer med plane flater (ca. 4 s, under 1 GB; den gamle
    kanten av hoydefelt minus nedgangen brukte over 6 GB i clean())."""
    out_pl, in_pl = lip_planforms()
    outer = _plan_prism(out_pl, -30.0, P.LIP_H, x_max=P.LIP_X1)
    inner = _plan_prism(in_pl, -40.0, P.LIP_H + 10.0, x_max=P.LIP_X1 + 60.0)
    return outer.cut(inner, clean=False)


def groove() -> cq.Workplane:
    """Sporet i lokkets underside: kanten med LID_CLEAR klaring paa sidene
    og LID_CLEAR_TOP over toppen."""
    out_pl, in_pl = groove_planforms()
    top = P.LIP_H + P.LID_CLEAR_TOP
    outer = _plan_prism(out_pl, -60.0, top, x_max=P.LIP_X1 + P.LID_CLEAR)
    inner = _plan_prism(in_pl, -70.0, top + 10.0, x_max=P.LIP_X1 + 100.0)
    return outer.cut(inner, clean=False)


# ------------------------------------------------- hulrom under sprayhooden
def _box(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def cove() -> cq.Workplane:
    """Rommet under sprayhooden aktenfor ruffen, over karmen og bronnen.

    Fra karmens forkant (minus klaring) og innenfor karmens ytterkant
    (pluss klaring). Taket ligger LID_CLEAR over karmens hoeyeste topp ved
    kantene og stiger 45 grader akterover og innover fra sprayhoodens bein,
    regnet fra skjoeteplanet (som er platen ved print). Bare plane flater."""
    g = P.LID_CLEAR
    x_f = P.COCKPIT_X0 - P.COAMING_FWD - g
    x_e = P.SPRAY_X1 + 100.0
    y_s = P.COAMING_HALF_W + g
    h = max(D.coaming_top_z(float(x)) + g - split_z(float(x))
            for x in np.linspace(x_f + g, x_e, 80))
    zlo = min(split_z(x_f), split_z(x_e)) - 100.0
    box = _box(x_f, x_e, -y_s, y_s, zlo, 2400.0)
    xa, xb = x_f - 50.0, x_e + 50.0
    ramp = lambda x: split_z(x) + h + (x - x_f)
    front = (cq.Workplane("XZ")
             .polyline([(xa, zlo - 50.0), (xb, zlo - 50.0), (xb, ramp(xb)), (xa, ramp(xa))])
             .close().extrude(y_s + 100.0, both=True))

    def sec(x):
        Y = y_s + 50.0
        zr = lambda y: split_z(x) + h + (y_s - abs(y))
        pts = [(-Y, zlo - 50.0), (Y, zlo - 50.0), (Y, zr(Y)), (0.0, zr(0.0)), (-Y, zr(-Y))]
        return cq.Wire.makePolygon([cq.Vector(x, y, z) for y, z in pts], close=True)

    side = cq.Workplane("XY").newObject([cq.Solid.makeLoft([sec(xa), sec(xb)], ruled=True)])
    return box.intersect(front).intersect(side)


# ------------------------------------------------------------- lokket
def lid_raw() -> cq.Workplane:
    """Det som hoerer til lokket foer det kappes: ruffen, lukene,
    takventilen og sprayhooden."""
    out = D.coachroof()
    out = out.union(D.hatches())
    out = out.union(D.vents(where_only="roof"))
    out = out.union(D.sprayhood())
    return out


def mast_hole() -> cq.Workplane:
    """Hull for masten gjennom lokket (masten limes i lokket og staar
    ned i mastestoetten)."""
    x = P.MAST_STEP_X
    z = D.roof_z(x)
    return (cq.Workplane("XY").workplane(offset=z - 400.0).center(x, 0.0)
            .ellipse(0.5 * P.MAST_HOLE_X, 0.5 * P.MAST_HOLE_Y).extrude(600.0))


def companion_shaft() -> cq.Workplane:
    """Nedgangen gjennom lokket, helt ned under skjoeten (man ser ned i
    kahytten gjennom nedgangen)."""
    return D.companionway_cut(z0=split_z(P.COACH_X1) - 150.0)


def _vol(w) -> float:
    """Presist volum (OCCs raske Volume() bommer med 5-7 L paa lokket)."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps

    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(w.val().wrapped, g, 1e-6, False)
    return g.Mass()


def _inside(w: cq.Workplane, p) -> bool:
    """Punktet p ligger inni volumet (uavhengig av de boolske operasjonene)."""
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_IN

    cl = BRepClass3d_SolidClassifier(w.val().wrapped, gp_Pnt(*[float(v) for v in p]), 1e-3)
    return cl.State() == TopAbs_IN


def _checked_cut(w: cq.Workplane, tool: cq.Workplane, what: str, probes=()) -> cq.Workplane:
    """Kutt som sjekkes mot volumet av overlappet OG mot proeve-punkter.
    OCC kan returnere et gyldig volum der kuttet ikke er gjort (sett 13.11:
    nedgangen etter hulrommet i det gamle lokket forsvant uten feilmelding).
    Da feilet ogsaa w.intersect(tool) (0 L), saa volumsammenligningen alene
    slipper feilen gjennom; proeve-punktene (inni baade w og verktoeyet foer
    kuttet, utenfor etterpaa) fanger den."""
    for p in probes:
        if not (_inside(w, p) and _inside(tool, p)):
            raise RuntimeError(f"lokket: proeve-punktet {p} for '{what}' ligger ikke i delen og verktoeyet")
    expect = _vol(w.intersect(tool))
    out = w.cut(tool)
    got = _vol(w) - _vol(out)
    n = len(out.solids().vals())
    missed = [p for p in probes if _inside(out, p)]
    if n != 1 or not out.val().isValid() or missed or abs(got - expect) > 0.01 * expect + 5.0e4:
        raise RuntimeError(f"lokket: kuttet '{what}' feilet (solider {n}, fjernet "
                           f"{got / 1e6:.2f} L, ventet {expect / 1e6:.2f} L, punkter igjen {missed})")
    return out


def _lid_probes():
    """Ett eller to punkter per kutt som maa vaere fjernet fra lokket."""
    sz = split_z
    go, gi = groove_planforms()
    xg = 0.5 * (go.p[0, 0] + P.LIP_X1)
    yg = 0.5 * (go.half_width(xg) + gi.half_width(xg))
    xm = P.MAST_STEP_X
    xc = 0.5 * (P.COCKPIT_X0 + P.SPRAY_X1)
    xs = P.COACH_X1 - 100.0
    return {
        "groove": [(xg, yg, sz(xg) + 0.5 * (P.LIP_H + P.LID_CLEAR_TOP))],
        "mast": [(xm, 0.0, sz(xm) + 50.0)],
        "cove": [(xc, 0.0, sz(xc) + 20.0)],
        "shaft": [(xs, 0.0, sz(xs) + 60.0), (xs, 0.0, D.roof_z(P.COACH_X1) + 100.0)],
    }


def lid() -> cq.Workplane:
    """Ruff-taket som egen del, i byggekoordinater. Undersiden er
    skjoeteplanet; printes paa den (export dreier lokket print_tilt_deg()
    om Y)."""
    pr = _lid_probes()
    w = lid_raw().intersect(above_split())
    w = _checked_cut(w, groove(), "spor for kanten", pr["groove"])
    w = _checked_cut(w, mast_hole(), "mastehull", pr["mast"])
    w = _checked_cut(w, cove(), "rom under sprayhooden", pr["cove"])
    w = _checked_cut(w, companion_shaft(), "nedgang", pr["shaft"])
    return w


def companion_slot() -> cq.Workplane:
    """Paa skroget: nedgangen ned i kahytten, fra aapningens akterkant til
    LID_CLEAR foran karmen, like bred som nedgangen minus LID_CLEAR. Bunnen
    ligger 100 mm over oeverste trinn (INT_STEP_PROFILE), inne i kahytten."""
    op = opening_planform()
    x0 = float(op.p[-1, 0]) - 10.0
    x1 = P.COCKPIT_X0 - P.COAMING_FWD - P.LID_CLEAR
    hw = 0.5 * P.COMPANION_W - P.LID_CLEAR
    z0 = P.INT_STEP_PROFILE[-1][1] + 100.0
    z1 = split_z(x0) + 100.0
    return _box(x0, x1, -hw, hw, z0, z1)


# ------------------------------------------------------- paa skroget
def collar() -> cq.Workplane:
    """Det som staar igjen paa skroget av ruffen og sprayhooden under
    skjoeten, med kanten paa. Unioneres inn i skroget (build.py)."""
    c = lid_raw().cut(above_split())
    return c.union(lip())
