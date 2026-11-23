"""Innredningen i kahytten, printet i ett med skroget og uten support.

Kahytten er et HULROM som skjaeres ut av et massivt skrog. Alt som ikke er
hulrom - bunnen under durken, koyene, sofaene, benkene, skottene, skapene -
blir staaende som massivt materiale og printes med fyll. Da hviler hver
flate paa noe under seg, og det er bare hulrommets tak som kan henge:

* Under sidedekkene og fordekket heller taket 45 grader (en kile fra
  kanten av aapningen i dekket ned mot skrogsiden; foran og akter for
  aapningen en rampe). Kilen er skap og hyller under sidedekket.
* Over vinduene er kilen tatt bort, saa man ser inn i salongen; der baerer
  sidedekket seg selv som en bru mellom skapene foran og akter for
  vinduet (ca. 42 mm i 1:30). WIN_TIE gir en stoette midt i.
* Skott er mellomrommene mellom rommene. Doerene gaar helt opp, saa de
  ikke har overligger - taket over kahytten er lokket.

Innredningen er prismer som staar paa bunnen (ingen overheng), bordet har
45 graders underside ned mot en fot. Alt i fullskala-mm i byggekoordinater:
x fra baugen, y styrbord +, z over DWL. Maalene er fra Enderleins tegning
448-5 (1:15) og brosjyren (1:50); se params.py, INT_*.

Byggerekkefoelge (build.py, med P.CABIN):
  1. bare kragen under skjoeten og kanten (cabin.collar) settes paa
     skroget - hele ruffen unioneres ikke,
  2. aapningen i dekket (opening_cut) skjaeres ut,
  3. uthulingen faar keep_block(), saa kamrene ikke roerer kahytten,
  4. cabin_void(with_opening=False) skjaeres ut (rom, innredning, doerer),
  5. window_holes() aapner vinduene gjennom skrogveggen.
"""
from __future__ import annotations

import functools
import math

import cadquery as cq
import numpy as np

from . import cabin as CB
from . import curves as C
from . import deckhouse as D
from . import params as P
from . import shell as S

BIG = 1600.0          # "langt utenfor" i y og z (skroget er 1 340 bredt, dekket under 1 260 hoyt)
W_MIN = 2.0           # minste halve bredde paa kilens topp (unngaar null-kanter)
RAMP_MIN = 80.0       # rampen forut stopper der den er saa hoy over koya
GAP = 1.0             # smaa forskyvninger saa flater ikke faller sammen (OCC ga
                      # tomme resultat naar aapningens sider gikk gjennom kilens kant)


# ------------------------------------------------------------ hjelpere
def _box(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def _prism(pts, z0, z1) -> cq.Workplane:
    """Mangekant i plan (x, y), ekstrudert fra z0 til z1."""
    return (cq.Workplane("XY").workplane(offset=z0)
            .polyline([(float(a), float(b)) for a, b in pts]).close().extrude(z1 - z0))


def _both(wp: cq.Workplane) -> cq.Workplane:
    """Styrbord-delen og speilbildet til babord."""
    return wp.mirror("XZ", union=True)


def _union(parts):
    out = None
    for p in parts:
        if p is not None:
            out = p if out is None else out.union(p)
    return out


def _wall() -> float:
    return P.HULL_WALL + P.VOID_MARGIN


@functools.lru_cache(maxsize=None)
def y_in(x: float, z: float) -> float:
    """Skrogets innside (halvbredde) i hoyden z ved x, med samme vegg og
    margin som uthulingen. 0 under bunnen."""
    pts = C.section_inner(float(x), _wall(), P.DECK_THICK, n=80)
    if pts is None:
        return 0.0
    a = np.asarray(pts)
    if z <= a[0, 1]:
        return 0.0
    if z >= a[-1, 1]:
        return float(a[-1, 0])
    for i in range(len(a) - 1):
        z0, z1 = a[i, 1], a[i + 1, 1]
        if (z0 - z) * (z1 - z) <= 0.0 and z1 != z0:
            f = (z - z0) / (z1 - z0)
            return float(a[i, 0] + f * (a[i + 1, 0] - a[i, 0]))
    return float(a[-1, 0])


# ------------------------------------------------------- aapningen i dekket
_OPEN = None


def opening_plan() -> D._Planform:
    """Aapningen i dekket: innenfor kanten som lokket tres over
    (cabin.opening_planform)."""
    global _OPEN
    if _OPEN is None:
        _OPEN = CB.opening_planform()
    return _OPEN


@functools.lru_cache(maxsize=None)
def ceiling_ref(x: float):
    """(w, z): hulrommets tak ved x er flatt i hoyden z for |y| <= w og
    heller saa 45 grader ned mot skrogsiden. Innenfor aapningen er w
    aapningens halve bredde og z dekkets underside ved kanten. Foran og
    akter for aapningen fortsetter det som en 45 graders rampe."""
    pl = opening_plan()
    xf, xa = float(pl.p[0, 0]), float(pl.p[-1, 0])
    xc = min(max(x, xf + 1e-3), xa - 1e-3)
    w = max(pl.half_width(xc), W_MIN)
    z = C.deck_z(xc, w) - P.DECK_THICK
    z -= max(0.0, xf - x) + max(0.0, x - xa)
    return w, z


def vberth_x0() -> float:
    """Der rampen under fordekket er RAMP_MIN over koya."""
    pl = opening_plan()
    xf = float(pl.p[0, 0])
    return xf - (ceiling_ref(xf)[1] - P.INT_VBERTH_Z - RAMP_MIN)


def _stations(x0: float, x1: float, step: float = 100.0):
    """Stasjoner fra x0 til x1: aapningens egne (tette rundt den rundede
    fronten og akterhjornene), aapningens ender, og jevnt ellers."""
    pl = opening_plan()
    xf, xa = float(pl.p[0, 0]), float(pl.p[-1, 0])
    xs = {x0, x1, xf, xa - 1e-3, xa}
    xs.update(x for x in CB._stations_for(pl) if x0 < x < x1)
    xs.update(np.arange(x0, x1, step).tolist())
    xs = sorted(x for x in xs if x0 <= x <= x1)
    out = [xs[0]]
    for x in xs[1:]:
        if x - out[-1] > 2.0:
            out.append(x)
    if out[-1] != x1:
        out[-1] = x1
    return out


def ceiling_wedge(x0: float, x1: float, z_low: float) -> cq.Workplane:
    """Volumet under det 45 graders taket: trapeser loftet med rette
    flater (ruled). Med rette flater mellom snitt som alle heller 45
    grader, heller hele flaten 45 grader."""
    wires = []
    for x in _stations(x0, x1):
        w, zt = ceiling_ref(x)
        W = w + (zt - z_low)
        pts = [(-W, z_low), (W, z_low), (w, zt), (-w, zt)]
        wires.append(cq.Wire.makePolygon([cq.Vector(x, y, z) for y, z in pts], close=True))
    solid = cq.Solid.makeLoft(wires, ruled=True)
    if not solid.isValid():
        raise RuntimeError("taket i kahytten ga et ugyldig volum")
    return cq.Workplane("XY").newObject([solid])


def inner_loft(x0: float, x1: float, step: float = 80.0) -> cq.Workplane:
    """Skrogets innside (vegg + margin, dekkets underside) mellom x0 og x1."""
    n = max(2, int(math.ceil((x1 - x0) / step)) + 1)
    xs = np.linspace(x0, x1, n)
    wires = [S._inner_wire(float(x), _wall(), P.DECK_THICK) for x in xs]
    if any(w is None for w in wires):
        raise RuntimeError("skrogets innside mangler snitt i kahytten")
    solid = cq.Solid.makeLoft(wires, ruled=True)
    if not solid.isValid():
        raise RuntimeError("skrogets innside ga et ugyldig volum")
    return cq.Workplane("XY").newObject([solid])


def opening_cut() -> cq.Workplane:
    """Aapningen gjennom dekket og kragen: aapningens omriss fra hulrommets
    flate tak (dekkets underside ved kanten, minus 1 mm) til godt over
    kanten. Loftet med rette flater gjennom de samme stasjonene som kilen,
    saa kilens topp og aapningen faller sammen. Kordene ligger innenfor
    det buede omrisset, saa kanten (cabin.lip) blir ikke roert."""
    pl = opening_plan()
    xf, xa = float(pl.p[0, 0]), float(pl.p[-1, 0])
    wires = []
    for x in _stations(xf, xa - 1e-3):
        w, zr = ceiling_ref(x)
        zt = C.deck_z(x, 0.0) + P.LID_LIFT + P.LIP_H + 200.0
        wo = max(w - 0.5 * GAP, 0.5 * W_MIN)
        pts = [(-wo, zr - 3.0 * GAP), (wo, zr - 3.0 * GAP), (wo, zt), (-wo, zt)]
        wires.append(cq.Wire.makePolygon([cq.Vector(x, y, z) for y, z in pts], close=True))
    solid = cq.Solid.makeLoft(wires, ruled=True)
    if not solid.isValid():
        raise RuntimeError("aapningen i dekket ga et ugyldig volum")
    return cq.Workplane("XY").newObject([solid])


# ------------------------------------------------------------- rommene
def rooms():
    """(navn, x0, x1, gulv) for hvert rom, mellom skottene."""
    t = 0.5 * P.INT_BH_T
    return [
        ("forpigg", vberth_x0(), P.INT_BH_WC_FWD - t, P.INT_VBERTH_Z),
        ("toalettrom", P.INT_BH_WC_FWD + t, P.INT_BH_WC_AFT - t, P.INT_WC_FLOOR_Z),
        ("salong", P.INT_BH_WC_AFT + t, P.INT_AFT_X, P.INT_SOLE_Z),
    ]


def doors() -> cq.Workplane:
    """Doeraapningene, fra terskelen og helt opp (ingen overligger)."""
    t = 0.5 * P.INT_BH_T + 10.0
    top = BIG
    out = []
    for xb, (ya, yb), sill in (
        (P.INT_BH_WC_FWD, P.INT_DOOR_FWD, P.INT_VBERTH_Z),
        (P.INT_BH_WC_AFT, P.INT_DOOR_AFT, P.INT_WC_FLOOR_Z),
    ):
        out.append(_box(xb - t, xb + t, ya, yb, sill, top))
    return _union(out)


def window_extension() -> cq.Workplane:
    """Over hylla ved vinduet er kilen tatt bort, saa man ser inn (kappes
    ved skrogets innside sammen med resten av hulrommet)."""
    return _box(P.WIN_X0, P.WIN_X1, -BIG, BIG, P.INT_SHELF_Z, BIG)


# ---------------------------------------------------------- innredningen
def _hull_band(x0, x1, yfun, z0, z1, n=24) -> cq.Workplane:
    """Styrbord: alt utenfor y = yfun(x) mellom x0 og x1 (skrogsiden
    kapper resten, siden dette trekkes fra hulrommet)."""
    xs = np.linspace(x0, x1, n)
    pts = [(x, yfun(x)) for x in xs] + [(x1, BIG), (x0, BIG)]
    return _prism(pts, z0, z1)


def _settees(z_low):
    t = 0.5 * P.INT_BH_T
    xa = P.INT_BH_WC_AFT + t
    yb = lambda x: max(y_in(x, P.INT_BACK_REF_Z) - P.INT_BACK_T, P.INT_SEAT_FRONT + 60.0)
    stb = _box(xa, P.INT_AFT_X, P.INT_SEAT_FRONT, BIG, z_low, P.INT_SEAT_Z).union(
        _hull_band(xa, P.INT_AFT_X, yb, z_low, P.INT_SHELF_Z))
    port = _box(xa, P.INT_GALLEY_X0, P.INT_SEAT_FRONT, BIG, z_low, P.INT_SEAT_Z).union(
        _hull_band(xa, P.INT_GALLEY_X0, yb, z_low, P.INT_SHELF_Z))
    return stb.union(port.mirror("XZ"))


def _galley(z_low, z_high):
    """Byssa babord: komfyrskapet, benken akter for det og veggskapene
    under sidedekket. Bygges paa styrbord og speiles."""
    x0, x1, xe = P.INT_GALLEY_X0, P.INT_GALLEY_X1, P.INT_AFT_X
    f0, f1 = P.INT_GALLEY_FRONT
    block = _prism([(x0, f0), (x1, f0), (x1, f1), (xe, f1), (xe, BIG), (x0, BIG)],
                   z_low, P.INT_COUNTER_Z)
    sx0, sx1, sy0, sy1, sd = P.INT_STOVE
    block = block.cut(_box(sx0, sx1, sy0, sy1, P.INT_COUNTER_Z - sd, P.INT_COUNTER_Z + 100.0))
    return block.mirror("XZ")


def _lockers(z_low, z_high):
    """Skap under sidedekket akter for INT_LOCKER_X0, begge sider: forkanten
    loddrett under aapningens kant, saa de baerer sidedekket."""
    yl = lambda x: ceiling_ref(x)[0] + GAP
    stb = _hull_band(P.INT_LOCKER_X0, P.INT_AFT_X, yl, z_low, z_high)
    return _both(stb)


def _table(z_low):
    x0, x1, hw, top = P.INT_TABLE
    e, fin = P.INT_TABLE_EDGE, P.INT_TABLE_FIN
    xa = P.INT_BH_WC_AFT + 0.5 * P.INT_BH_T
    if not P.INT_TABLE_LEAVES_UP:
        hw = P.INT_TABLE_FOLDED_HW
        body = _box(x0, x1, -hw, hw, z_low, top)
        return body.union(_box(xa, x0 + 1.0, -fin, fin, z_low, top - 200.0))
    za = top - e - (hw - fin)                      # der 45 graders undersiden moeter foten
    prof = [(-hw, top), (hw, top), (hw, top - e), (fin, za), (fin, z_low),
            (-fin, z_low), (-fin, za), (-hw, top - e)]
    v = (cq.Workplane("YZ").workplane(offset=x0).polyline(prof).close().extrude(x1 - x0))
    plan = (cq.Workplane("XY").workplane(offset=z_low - 1.0)
            .center(0.5 * (x0 + x1), 0.0).rect(x1 - x0, 2.0 * hw)
            .extrude(top - z_low + 2.0).edges("|Z").fillet(60.0))
    v = v.intersect(plan)
    # foten fortsetter fram til skottet og stoetten
    return v.union(_box(xa, x0 + 1.0, -fin, fin, z_low, za))


def _steps(z_low):
    prof = [(P.INT_STEP_PROFILE[0][0], z_low)] + list(P.INT_STEP_PROFILE) + [
        (P.INT_AFT_X, P.INT_STEP_PROFILE[-1][1]), (P.INT_AFT_X, z_low)]
    return (cq.Workplane("XZ").polyline(prof).close()
            .extrude(P.INT_STEP_HW, both=True))


def _wc_room(z_low, z_high):
    t = 0.5 * P.INT_BH_T
    xa, xb = P.INT_BH_WC_FWD + t, P.INT_BH_WC_AFT - t
    # Skapet babord: under taket som en kloss fra skapfronten, over taket bare
    # utenfor aapningens kant + GAP (som veggskapene og speilskapet). Ellers
    # faller skapets topp sammen med takkanten ved aapningen, og kuttet ga en
    # loesrevet flis (0 cm3) ved x 2925-3000 etter dekkslinje-rettingen (kryssjekk 13.11).
    zc = min(ceiling_ref(float(x))[1] for x in np.linspace(xa, xb, 25)) - 3.0 * GAP
    locker = _box(xa, xb, -BIG, -P.INT_WC_LOCKER_Y, z_low, zc).union(
        _hull_band(xa, xb, lambda x: ceiling_ref(x)[0] + GAP, zc - 1.0, z_high, n=12).mirror("XZ"))
    wx, wy, ax, ay, wtop = P.INT_WC
    wc = (cq.Workplane("XY").workplane(offset=z_low).center(wx, wy)
          .ellipse(ax, ay).extrude(wtop - z_low))
    counter = _box(xa, xb, P.INT_BASIN_FRONT, BIG, z_low, P.INT_BASIN_Z)
    bx, by, bax, bay, bd = P.INT_BASIN
    basin = (cq.Workplane("XY").workplane(offset=P.INT_BASIN_Z - bd).center(bx, by)
             .ellipse(bax, bay).extrude(bd + 100.0))
    counter = counter.cut(basin)
    m0, m1 = P.INT_MIRROR_X
    mirror = _hull_band(m0, m1, lambda x: ceiling_ref(x)[0] + GAP, z_low, z_high, n=12)
    return locker.union(wc).union(counter).union(mirror)


def _post(z_low, z_high):
    """Mastestoetten: soeyle fra bunnen, med et hode rundt hullet for
    mastefoten (masten staar gjennom lokket og ned i stoetten)."""
    x, s = P.MAST_STEP_X, P.MAST_POST_W
    post = _box(x - 0.5 * s, x + 0.5 * s, -0.5 * s, 0.5 * s, z_low, z_high)
    if not P.INT_POST_SOCKET:
        return post
    zt = ceiling_ref(x)[1] - 3.0 * GAP               # stoettens topp (under aapningen)
    hx, hy = P.MAST_HOLE_X + 2.0 * P.SCALE, P.MAST_HOLE_Y + 2.0 * P.SCALE
    z_hole = D.roof_z(x) - P.MAST_SOCKET          # mastefoten: stopp naar masten limes i lokket
    zh = min(z_hole - 2.0 * P.SCALE, zt - 120.0)     # hodet begynner her
    flare = 0.5 * max(hx - s, hy - s)                # 45 graders overgang
    head = (cq.Workplane("XY").workplane(offset=zh - flare).center(x, 0.0).rect(s, s)
            .workplane(offset=flare).rect(hx, hy).loft())
    head = head.union(_box(x - 0.5 * hx, x + 0.5 * hx, -0.5 * hy, 0.5 * hy, zh, z_high))
    hole = (cq.Workplane("XY").workplane(offset=z_hole).center(x, 0.0)
            .ellipse(0.5 * P.MAST_HOLE_X, 0.5 * P.MAST_HOLE_Y).extrude(z_high - z_hole + 10.0))
    return post.union(head).cut(hole)


def _window_ties(z_low, z_high):
    """Valgfri stoette midt i vinduet (P.WIN_TIE): et tynt spant fra hylla
    opp under sidedekket, utenfor aapningen. Skjaeres bort etter print."""
    xm = 0.5 * (P.WIN_X0 + min(P.WIN_X1, P.INT_LOCKER_X0))
    h = 0.5 * P.WIN_TIE_W
    stb = _hull_band(xm - h, xm + h, lambda x: ceiling_ref(x)[0] + GAP, P.INT_SHELF_Z - 10.0,
                     z_high, n=2)
    return _both(stb)


def furniture() -> cq.Workplane:
    """Alt i kahytten som ikke er hulrom, minus aapningen i dekket."""
    z_low = min(P.INT_SOLE_Z, P.INT_WC_FLOOR_Z) - 200.0
    z_high = C.deck_z(P.INT_BH_WC_FWD, 0.0) + 200.0   # under toppen av aapningen
    parts = [
        _settees(z_low),
        _galley(z_low, z_high),
        _lockers(z_low, z_high),
        _table(z_low),
        _steps(z_low),
        _wc_room(z_low, z_high),
        _post(z_low, z_high),
    ]
    if P.WIN_TIE:
        parts.append(_window_ties(z_low, z_high))
    return _union(parts)


# ---------------------------------------------------------- til build.py
def keep_block() -> cq.Workplane:
    """Gis til uthulingen (shell.hollow, keep): kamrene skal ikke hule ut
    kahyttens omraade, som skal vaere massivt rundt hulrommet. Begynner
    paa et spant, saa det ikke blir smale kamre igjen foran."""
    x_need = vberth_x0() - 2.0 * P.SCALE
    ribs = [x for x in S.bulkhead_stations() if x <= x_need]
    x0 = ribs[-1] if ribs else P.VOID_FWD
    return _box(x0, P.COCKPIT_X0, -BIG, BIG, -BIG, BIG)


def cabin_void(log=None, with_opening: bool = True) -> cq.Workplane:
    """Hele hulrommet som skal skjaeres ut av skroget: rommene under
    45 graders taket, utvidelsen ved vinduene og doerene, minus
    innredningen, kappet ved skrogets innside - og aapningen i dekket.
    build.py skjaerer aapningen (opening_cut) som eget kutt foer
    uthulingen og bruker with_opening=False: aapningen i samme kutt som
    kahytten ga et ugyldig skrog naar kragen under lokket staar paa dekket.

    Rekkefoelgen holder de boolske operasjonene smaa: alt foer kappingen
    ved skrogets innside er plane flater (kile, kasser, prismer); bare den
    siste snittoperasjonen moeter de buede flatene. (Aa trekke innredningen
    fra et hulrom som alt var kappet ved innsiden brukte over 6 GB.)"""
    rs = rooms()
    x0, x1 = rs[0][1], rs[-1][2]
    z_low = min(r[3] for r in rs) - 100.0
    wedge = ceiling_wedge(x0 - 20.0, x1 + 20.0, z_low)
    raw = None
    for _, a, b, floor in rs:
        r = wedge.intersect(_box(a, b, -BIG, BIG, floor, BIG))
        raw = r if raw is None else raw.union(r)
    raw = raw.union(window_extension())
    raw = raw.union(doors())
    if log:
        log("    kahytt: rom under taket, vinduer, doerer")
    opening = opening_cut()
    furn = furniture().cut(opening)
    raw = raw.cut(furn)
    if log:
        log("    kahytt: innredning trukket fra")
    void = raw.intersect(inner_loft(x0 - 20.0, x1 + 20.0))
    if log:
        log("    kahytt: kappet ved skrogets innside")
    if not with_opening:
        return void.clean()
    void = void.union(opening)
    if log:
        log("    kahytt: aapningen i dekket")
    return void.clean()


def window_holes() -> cq.Workplane:
    """Glasset i vinduene som aapninger gjennom skrogveggen: omrisset
    trukket inn WIN_FRAME (rammen blir staaende som forsenkningen), bare
    gjennom veggen - innenfor ligger hulrommet."""
    box = D._window_box(-P.WIN_FRAME)
    depth = P.HULL_WALL + P.VOID_MARGIN + 20.0
    inner = D._inside_loft(depth, P.WIN_X0 - 200.0, P.WIN_X1 + 200.0, n=16)
    cut = box.cut(inner)
    if P.WIN_TIE:
        xm = 0.5 * (P.WIN_X0 + min(P.WIN_X1, P.INT_LOCKER_X0))
        cut = cut.cut(_box(xm - 0.5 * P.WIN_TIE_W, xm + 0.5 * P.WIN_TIE_W,
                           -4000.0, 4000.0, -BIG, BIG))   # vindusboksen gaar 3 000 ut
    return cut
