"""Ruff, luker, ventiler, nedgang, vindu i skrogsiden, sprayhood og cockpit.

Hoyder og lengder er fra profiltegningen 1:50, bredder fra dekksplanen.
Ruffen er lav og bred paa et flatt fordekk; vinduet sitter i skrogsiden,
i baandet mellom fenderlisten og dekkskanten. Se README under "Merk om
ruffen".

Ruffen og sprayhooden bygges som hoydefelt over et omriss i plan: hoyden
over underlaget er en profil av avstanden innover fra omrisset - en skraa
side som runder av over i taket. Da faar den skraa fronten, sidene og
takkanten sin avrunding direkte i formen; fillet paa disse flatene gir
ugyldige volumer i OCC. Volumet loftes gjennom tverrsnitt. Smaa, frie
klosser (luker, karm) avrundes med fillet, som virker der.
"""
from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from . import curves as C
from . import params as P
from . import shell as S

deck_z = C.deck_z


# ---------------------------------------------------------------- kurver
def _knee_table(table, x: float, blend: float) -> float:
    """Rette streker gjennom punktene i `table`, der hvert indre knekkpunkt
    er rundet av med en parabel over +-blend mm (glatt, C1). Utenfor
    blandesonene er verdiene de samme som for rette streker; utenfor
    tabellen fortsetter endestykkene rett ut."""
    xs = [t[0] for t in table]
    ys = [t[1] for t in table]
    s = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(len(xs) - 1)]
    i = min(max(int(np.searchsorted(xs, x)) - 1, 0), len(s) - 1)
    y = ys[i] + s[i] * (x - xs[i])
    for k in range(1, len(xs) - 1):
        L = min(blend, 0.45 * (xs[k] - xs[k - 1]), 0.45 * (xs[k + 1] - xs[k]))
        u = x - (xs[k] - L)
        if 0.0 < u < 2.0 * L:
            y = ys[k] + s[k - 1] * (x - xs[k]) + (s[k] - s[k - 1]) * u * u / (4.0 * L)
    return float(y)


def _smoothstep(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def _smax(a: float, b: float, k: float) -> float:
    """Glatt maksimum: som max(a, b), men uten knekk der a og b er like."""
    h = max(k - abs(a - b), 0.0) / k
    return max(a, b) + h * h * k / 4.0


def _smin(a: float, b: float, k: float) -> float:
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k / 4.0


def _roof_line(x: float) -> float:
    """Takets hoyde paa senterlinjen, glatt og uten endestopp (brukes av
    selve ruffen, som gaar litt forbi tabellens ender)."""
    return _knee_table(P.COACH_TOP, x, P.COACH_TOP_BLEND)


def roof_z(x: float) -> float:
    """Den hoye ruffens topp paa senterlinjen."""
    return _roof_line(min(max(x, P.COACH_X0), P.COACH_X1))


coach_roof_z = roof_z   # eldre navn, brukes av fittings og rig


def roof_surface_z(x: float, y: float) -> float:
    """Rufftakets hoyde ved (x, y): takbuen tvers over."""
    return _roof_line(x) - P.COACH_ROOF_CAMBER * (y / 1500.0) ** 2


def coach_half_width(x: float) -> float:
    """Ruffens halvbredde ved dekket: dekkshalvbredden minus sidedekket,
    med rundet front fra STEP_X0 og COACH_FRONT_R akterover."""
    w = max(P.COACH_MIN_HALF_W, C.deck_half_breadth(x) - P.SIDEDECK)
    R = P.COACH_FRONT_R
    if x < P.STEP_X0 + R:
        u = (P.STEP_X0 + R - x) / R
        w *= math.sqrt(max(0.0, 1.0 - u * u))
    return w


_COAMING_XM = 0.5 * (P.COAMING_TOP_Z[0][0] + P.COAMING_TOP_Z[-1][0])
_COAMING_FIT = np.polyfit([p[0] - _COAMING_XM for p in P.COAMING_TOP_Z],
                          [p[1] for p in P.COAMING_TOP_Z], 2)


def coaming_top_z(x: float) -> float:
    """Cockpitkarmens overkant over DWL.

    En glatt kurve (andregrads, innen 5 mm av punktene) gjennom den maalte
    tabellen COAMING_TOP_Z, men aldri lavere enn COAMING_MIN_H over dekket
    ved karmens ytterkant (dekksbuen loefter dekket innenfor dekkskanten) -
    begge deler blandet uten knekk. Fra COAMING_DOWN_X glir karmen jevnt ned
    i dekket fram til COAMING_X1; aktenfor det er "karmtoppen" dekkskanten.
    """
    if x >= P.COAMING_X1:
        return C.sheer_z(x)
    zt = float(np.polyval(_COAMING_FIT, x - _COAMING_XM))
    floor = deck_z(x, coaming_half_width(x)) + P.COAMING_MIN_H
    z = _smax(zt, floor, 20.0)
    t = _smoothstep((x - P.COAMING_DOWN_X) / (P.COAMING_X1 - P.COAMING_DOWN_X))
    return z * (1.0 - t) + C.sheer_z(x) * t


# --------------------------------------------------------------- hjelpere
def _roof_body(x0, x1, top_at, half_w: float, depth: float, camber: float,
               steps: int = 12) -> cq.Workplane:
    """Volum begrenset oppe av en (eventuelt buet) takflate, ellers rikelig stort."""
    wires = []
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


def _rounded_block(x0, x1, w, z0, z1, rad, top_fillet=0.0) -> cq.Workplane:
    """Kloss med avrundede hjorner i plan og (valgfritt) avrundet overkant.
    Filleten legges paa den frie klossen, foer den unioneres inn."""
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
    if top_fillet > 0:
        b = _try_fillet(b, b.faces(">Z").edges(), top_fillet)
    return b


def _try_fillet(wp: cq.Workplane, edges: cq.Workplane, r: float) -> cq.Workplane:
    """Fillet som bare brukes hvis resultatet er ett gyldig volum som
    ikke har vokst; ellers beholdes delen som den var."""
    try:
        out = edges.fillet(r)
        s = out.val()
        if s.isValid() and len(out.solids().vals()) == 1 \
                and s.Volume() <= wp.val().Volume() + 1.0:
            return out
    except Exception:  # pragma: no cover - fillet feilet, behold kanten
        pass
    return wp


# ------------------------------------------- hoydefelt over et omriss i plan
class _Planform:
    """Et omriss i plan, styrbord halvdel, som tett polylinje fra spissen
    forut (paa senterlinjen) akterover langs siden. x maa vokse langs
    linjen. Gir fortegnsavstanden til omrisset (positiv innenfor) og hvor
    mye omrisset vender forover der (1 = rett forover, 0 = til siden)."""

    def __init__(self, pts):
        p = np.asarray(pts, dtype=float)
        self.p = p
        self.a = p[:-1]
        self.ab = p[1:] - p[:-1]
        self.L2 = np.maximum(np.einsum("ij,ij->i", self.ab, self.ab), 1e-12)
        L = np.sqrt(self.L2)
        nseg = np.c_[-self.ab[:, 1], self.ab[:, 0]] / L[:, None]   # utover
        nv = np.zeros_like(p)
        nv[:-1] += nseg
        nv[1:] += nseg
        self.nv = nv / np.maximum(np.linalg.norm(nv, axis=1), 1e-12)[:, None]

    def half_width(self, x: float) -> float:
        if x < self.p[0, 0] or x > self.p[-1, 0]:
            return 0.0
        return float(np.interp(x, self.p[:, 0], self.p[:, 1]))

    def field(self, x: float, ys):
        q = np.c_[np.full(len(ys), x), np.abs(ys)]
        aq = q[:, None, :] - self.a[None, :, :]
        t = np.clip(np.einsum("kij,ij->ki", aq, self.ab) / self.L2[None, :], 0.0, 1.0)
        diff = aq - t[:, :, None] * self.ab[None, :, :]
        dd = np.einsum("kij,kij->ki", diff, diff)
        i = np.argmin(dd, axis=1)
        k = np.arange(len(ys))
        d = np.sqrt(dd[k, i])
        ti = t[k, i]
        n = (1.0 - ti)[:, None] * self.nv[i] + ti[:, None] * self.nv[i + 1]
        n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
        inside = np.abs(ys) < self.half_width(x)
        return np.where(inside, d, -d), np.clip(-n[:, 0], 0.0, 1.0)


def _edge_profile(d, H, beta, R):
    """Hoyde over underlaget i avstanden d innenfor omrisset: en skraa
    side (vinkel beta fra vannrett) som runder av med radius R over i
    taket i hoyden H. Utenfor omrisset (d < 0) fortsetter siden nedover."""
    sb, cb = np.sin(beta), np.cos(beta)
    p = (R + (H - R) * cb) / sb          # der buen moeter taket
    dw = p - R * sb                      # der siden gaar over i buen
    arc = H - R + np.sqrt(np.clip(R * R - (d - p) ** 2, 0.0, None))
    return np.where(d <= dw, d * np.tan(beta), np.where(d < p, arc, H))


def _resample(pts, n: int):
    """n punkter jevnt fordelt paa buelengden. Med like parametre i alle
    tverrsnitt (se _hf_wire) faar flaten jevn parametrisering - punkter
    tettere i rundingene ga splinesvingninger og flisete STL."""
    d = np.diff(pts, axis=0)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))])
    u = np.linspace(0.0, s[-1], n)
    return np.c_[np.interp(u, s, pts[:, 0]), np.interp(u, s, pts[:, 1])]


def _hf_section(x, plan, base, top, floor, angles, radii, n_half=80, y_pad=250.0):
    """Tverrsnitt av et hoydefelt ved x: styrbord halvdel som (y, z) fra
    senterlinjen ut til der flaten har gaatt under `floor` (begravd i
    underlaget). angles/radii er (forover, til siden)."""
    y_max = plan.half_width(x) + y_pad
    for _ in range(4):
        ys = np.linspace(0.0, y_max, 900)
        d, f = plan.field(x, ys)
        zb = np.array([base(x, y) for y in ys])
        H = np.array([top(x, y) for y in ys]) - zb
        f2 = f * f
        beta = np.radians(angles[1] + (angles[0] - angles[1]) * f2)
        R = radii[1] + (radii[0] - radii[1]) * f2
        z = zb + _edge_profile(d, H, beta, R)
        lim = np.array([floor(x, y) for y in ys])
        under = np.nonzero(z <= lim)[0]
        if len(under):
            break
        y_max *= 2.0            # butt front: snittet er bredere enn antatt
    if len(under) == 0 or under[0] < 2:
        raise ValueError(f"tverrsnitt ved x={x:.0f} naar ikke ned under underlaget")
    k = under[0]
    a = (z[k - 1] - lim[k - 1]) / ((z[k - 1] - lim[k - 1]) - (z[k] - lim[k]))
    end = (ys[k - 1] + a * (ys[k] - ys[k - 1]), z[k - 1] + a * (z[k] - z[k - 1]))
    pts = np.vstack([np.c_[ys[:k], z[:k]], [end]])
    return _resample(pts, n_half)


def _hf_wire(x: float, half, z_bot: float) -> cq.Wire:
    """Lukket tverrsnitt: flaten fra babord til styrbord som en spline
    (samme parametre i alle snitt), saa rett ned og tvers under."""
    full = np.vstack([half[::-1] * [-1.0, 1.0], half[1:]])
    vs = [cq.Vector(x, float(y), float(z)) for y, z in full]
    top = cq.Edge.makeSpline(vs, parameters=list(np.linspace(0.0, 1.0, len(vs))))
    a, b = vs[0], vs[-1]
    lb, la = cq.Vector(x, b.y, z_bot), cq.Vector(x, a.y, z_bot)
    return cq.Wire.assembleEdges([top, cq.Edge.makeLine(b, lb), cq.Edge.makeLine(lb, la),
                                  cq.Edge.makeLine(la, a)])


def _hf_solid(xs, plan, base, top, floor, angles, radii, what: str,
              y_scale=None) -> cq.Workplane:
    halves = [_hf_section(x, plan, base, top, floor, angles, radii) for x in xs]
    if y_scale is not None:
        halves = [h * [y_scale(x), 1.0] for x, h in zip(xs, halves)]
    z_bot = min(float(h[:, 1].min()) for h in halves) - 60.0
    wires = [_hf_wire(x, h, z_bot) for x, h in zip(xs, halves)]
    solid = cq.Solid.makeLoft(wires, ruled=False)
    if not solid.isValid():
        raise RuntimeError(f"{what}: loften ga et ugyldig volum")
    return cq.Workplane("XY").newObject([solid])


def _quarter_sections(x0: float, x1: float, n: int, power: float = 2.0):
    """n+1 stasjoner fra x0 til x1, tettest ved x0 (rundet ende der)."""
    return [x0 + (x1 - x0) * (i / n) ** power for i in range(n + 1)]


def _even_sections(x0: float, x1: float, step: float):
    """Stasjoner etter x0 til og med x1, med avstand hoyst `step`. Jevn
    avstand gir loften jevn parametrisering; store sprang i avstanden
    gir boelger mellom snittene."""
    n = max(1, int(math.ceil((x1 - x0) / step)))
    return [x0 + (x1 - x0) * i / n for i in range(1, n + 1)]


# ------------------------------------------------------------------- ruff
def _coach_planform() -> _Planform:
    """Ruffens fot mot dekket: rundet front fra STEP_X0 (ellipse over
    COACH_FRONT_R), sidene dekkshalvbredden minus sidedekket, og akter-
    hjorner rundet med COACH_RAD inn mot nedgangsskottet."""
    R, r = P.COACH_FRONT_R, P.COACH_RAD
    pts = []
    for th in np.linspace(0.0, 0.5 * math.pi, 61)[:-1]:
        x = P.STEP_X0 + R * (1.0 - math.cos(th))
        pts.append((x, coach_half_width(x)))
    xa = P.COACH_X1 - r
    for x in np.arange(P.STEP_X0 + R, xa, 25.0):
        pts.append((x, coach_half_width(x)))
    cy = coach_half_width(xa) - r
    for th in np.linspace(0.0, 0.5 * math.pi, 31):
        pts.append((xa + r * math.sin(th), cy + r * math.cos(th)))
    return _Planform(pts)


def _coach_stations():
    """Tverrsnittene: tette rundt den rundede fronten, jevnt fordelt midt
    paa (100 mm), og tette i akterhjornene. Det foerste ligger like bak
    spissen av fronten forlenget ned under dekket, og er helt begravd.
    Med 90/45 mm midt paa feilet unionen med skyveluken (volumet sank),
    mens 100, 120 og 160 mm virket."""
    bury = 35.0
    x_s = P.STEP_X0 - bury / math.tan(math.radians(P.COACH_FRONT_ANGLE)) + 4.0
    xm = P.STEP_X0 + P.COACH_FRONT_R
    xa = P.COACH_X1 - P.COACH_RAD
    xs = _quarter_sections(x_s, xm, 24)
    xs += _even_sections(xm, xa, 100.0)
    xs += [xa + P.COACH_RAD * math.sin(math.radians(a)) for a in (15, 30, 45, 60, 75)]
    return xs


def coachroof() -> cq.Workplane:
    """Ruffen: lav og bred, rundet front i plan, skraa front opp til taket
    og avrundet takkant hele veien rundt. Akterkanten (nedgangsskottet)
    er loddrett og ligger inne i sprayhooden."""
    plan = _coach_planform()
    return _hf_solid(
        _coach_stations(), plan,
        base=deck_z,
        top=roof_surface_z,
        floor=lambda x, y: deck_z(x, y) - 35.0,
        angles=(P.COACH_FRONT_ANGLE, P.COACH_SIDE_ANGLE),
        radii=(P.COACH_FRONT_EDGE_R, P.COACH_EDGE_R),
        what="ruff",
    )


def hatches() -> cq.Workplane:
    """Forluke foran masten og skyveluke over nedgangen, begge paa taket."""
    out = None
    for (x0, x1, w, h) in (P.FOREHATCH, P.SLIDE_HATCH):
        xm = 0.5 * (x0 + x1)
        zb = roof_z(xm) - P.COACH_ROOF_CAMBER - 20.0
        zt = roof_z(xm) + h
        b = _rounded_block(x0, x1, w, zb, zt, P.HATCH_RAD, top_fillet=P.HATCH_EDGE_R)
        out = b if out is None else out.union(b)
    return out


def vents(where_only: str | None = None) -> cq.Workplane:
    """Soppventiler: en paa fordekket, en paa taket bak masten. Med
    where_only ("deck" eller "roof") bare de som staar der."""
    out = None
    for x, where in P.VENTS:
        if where_only is not None and where != where_only:
            continue
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


def companionway_cut(z0: float | None = None) -> cq.Workplane:
    """Nedgangen: fordypning i ruffens bakkant, fra terskelen (eller z0)."""
    x = P.COACH_X1
    if z0 is None:
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
    viser. Endene kan vaere skraa (WIN_RAKE). `grow` gjor omrisset stoerre
    paa alle kanter."""
    rf, ra = getattr(P, "WIN_RAKE", (0.0, 0.0))
    x0, x1 = P.WIN_X0 - grow, P.WIN_X1 + grow
    lo = lambda x: C.strake_z(x) + P.WIN_ABOVE_STRAKE - grow
    hi = lambda x: C.sheer_z(x) - P.WIN_BELOW_DECK + grow
    pts = [(x0, lo(x0)), (x1, lo(x1)), (x1 - ra, hi(x1 - ra)), (x0 + rf, hi(x0 + rf))]
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
def _spray_half_w(x: float) -> float:
    """Sprayhoodens fot i plan: SPRAY_INSET innenfor ruffens side, og like
    bred aktenfor der ruffen begynner aa runde av."""
    return coach_half_width(min(x, P.COACH_X1 - P.COACH_RAD)) - P.SPRAY_INSET


def _spray_aft_scale(x: float) -> float:
    """Akterhjornene rundes i plan med halve SPRAY_AFT_R ved aa skalere de
    siste tverrsnittene i bredden. Rundes selve omrisset, ligger enden av
    det like ved det siste snittet og gir et hakk i flaten der."""
    u = x - (P.SPRAY_X1 - P.SPRAY_AFT_R)
    if u <= 0.0:
        return 1.0
    drop = 0.5 * (P.SPRAY_AFT_R - math.sqrt(max(P.SPRAY_AFT_R ** 2 - u * u, 0.0)))
    return 1.0 - drop / _spray_half_w(x)


def _spray_foot_z(x: float) -> float:
    """Hoyden profilen regnes fra: rufftaket ved foten, ogsaa aktenfor
    ruffen. Da har hooden samme form hele veien, og aktenfor ruffen gaar
    sidene bare rett videre ned til sidedekket (utenfor karmen)."""
    return roof_surface_z(x, _spray_half_w(x)) - 5.0


def _spray_top_z(x: float, y: float) -> float:
    """Sprayhoodens topp: svakt stigende akterover, buet tvers over, og
    rundet ned mot akterkanten."""
    t = (P.SPRAY_X1 - x) / (P.SPRAY_X1 - P.SPRAY_X0)
    z = P.SPRAY_TOP_Z - P.SPRAY_TOP_FALL * t
    z -= P.SPRAY_CAMBER * (y / max(_spray_half_w(x), 1.0)) ** 2
    u = x - (P.SPRAY_X1 - P.SPRAY_AFT_R)
    if u > 0.0:
        z -= P.SPRAY_AFT_R - math.sqrt(max(P.SPRAY_AFT_R ** 2 - u * u, 0.0))
    return z


def _spray_front_angle() -> float:
    """Frontens helning (grader) fra foten paa taket til toppens forkant."""
    rise = P.SPRAY_TOP_Z - P.SPRAY_TOP_FALL * (P.SPRAY_X1 - P.SPRAY_TOP_X0) \
        / (P.SPRAY_X1 - P.SPRAY_X0) - _spray_foot_z(P.SPRAY_X0)
    return math.degrees(math.atan2(rise, P.SPRAY_TOP_X0 - P.SPRAY_X0))


def _spray_planform() -> _Planform:
    L = P.SPRAY_FRONT_L
    pts = []
    for th in np.linspace(0.0, 0.5 * math.pi, 41)[:-1]:
        x = P.SPRAY_X0 + L * (1.0 - math.cos(th))
        pts.append((x, _spray_half_w(x) * math.sin(th)))
    # rett videre forbi akterkanten, saa omrissets ende ikke paavirker snittene
    for x in np.arange(P.SPRAY_X0 + L, P.SPRAY_X1 + 200.0, 20.0):
        pts.append((x, _spray_half_w(x)))
    return _Planform(pts)


def sprayhood() -> cq.Workplane:
    """Sprayhood over nedgangen, henger ut over cockpiten.

    Modellert massiv - i 1:30 ville veggene i en aapen kalesje blitt under
    en halv millimeter. Fronten heller som i profilen og er rundet i plan,
    skuldrene og akterkanten er runde. Siden fortsetter ned til dekket
    under foten, saa hooden aldri henger i luften der ruffen slutter.
    """
    plan = _spray_planform()
    ang = _spray_front_angle()
    bury = 40.0
    foot = lambda x, y: _spray_foot_z(x)
    floor = lambda x, y: deck_z(x, y) - bury
    # foerste snitt like bak spissen av fronten forlenget ned til dekket
    drop = _spray_foot_z(P.SPRAY_X0) - (deck_z(P.SPRAY_X0, 0.0) - bury)
    x_s = P.SPRAY_X0 - drop / math.tan(math.radians(ang)) + 4.0
    x_e = P.SPRAY_X1 - P.SPRAY_AFT_R * (1.0 - math.sin(math.radians(80.0)))
    xm = P.SPRAY_X0 + P.SPRAY_FRONT_L
    xa = P.SPRAY_X1 - P.SPRAY_AFT_R
    xs = _quarter_sections(x_s, xm, 22) + _even_sections(xm, xa, 45.0)
    xs += [xa + P.SPRAY_AFT_R * math.sin(math.radians(a)) for a in (20, 35, 48, 60, 70)] + [x_e]
    return _hf_solid(xs, plan, base=foot, top=_spray_top_z, floor=floor,
                     angles=(ang, P.SPRAY_SIDE_ANGLE),
                     radii=(P.SPRAY_FRONT_R, P.SPRAY_EDGE_R), what="sprayhood",
                     y_scale=_spray_aft_scale)


# --------------------------------------------------------------- cockpit
def cockpit_half_width(x: float) -> float:
    """Bronnens halvbredde langs sidene, forut for den bakre rundingen."""
    return max(200.0, _smin(P.COCKPIT_HALF_W, C.deck_half_breadth(x) - P.COCKPIT_INSET,
                            P.WIDTH_BLEND))


def coaming_half_width(x: float) -> float:
    return max(260.0, _smin(P.COAMING_HALF_W, C.deck_half_breadth(x) - 200.0, P.WIDTH_BLEND))


def _offset_stb(pts, d: float):
    """Forskyver en styrbord-kurve (x, y), som ender paa senterlinjen, `d`
    utover langs normalen. Kurven speiles forbi senterlinjen foer normalene
    regnes, saa enden blir riktig."""
    ext = list(pts) + [(x, -y) for (x, y) in reversed(pts[:-1])][:3]
    a = np.array(ext, dtype=float)
    g = np.gradient(a, axis=0)
    L = np.hypot(g[:, 0], g[:, 1])
    L[L < 1e-9] = 1.0
    out = a + d * np.c_[-g[:, 1] / L, g[:, 0] / L]
    out = out[: len(pts)]
    out[-1, 1] = 0.0
    return [(float(x), float(y)) for x, y in out]


def _cockpit_stb(grow: float = 0.0):
    """Bronnens omriss paa styrbord side: fra enden av det fremre hjornet
    (x = COCKPIT_X0 + COCKPIT_RAD) langs siden, rundt den maalte bakre
    rundingen (COCKPIT_AFT) til senterlinjen. `grow` forskyver omrisset
    utover (karet rundt bronnen)."""
    x0 = P.COCKPIT_X0 + P.COCKPIT_RAD
    x1 = P.COCKPIT_AFT[0][0]
    n = max(2, int((x1 - x0) / 60.0))
    xs = [x0 + (x1 - x0) * i / n for i in range(n)]
    pts = [(x, cockpit_half_width(x)) for x in xs]
    # aldri naermere dekkskanten enn 200 mm, uansett hva tabellen sier
    pts += [(x, min(y, C.deck_half_breadth(x) - 200.0)) for x, y in P.COCKPIT_AFT]
    if grow:
        pts = _offset_stb(pts, grow)
        pts[0] = (x0, pts[0][1])
    return pts


def _plan_prism_well(stb, x_fwd: float, rad: float, z0: float, z1: float) -> cq.Workplane:
    """Loddrett prisme av en speilsymmetrisk planform med rett forkant ved
    x_fwd og hjorneradius rad, der sidene er en spline gjennom styrbord-
    punktene `stb` (foerste punkt der det fremre hjornet slutter, siste paa
    senterlinjen akter) og speilbildet av dem."""
    w0 = stb[0][1]
    r = min(rad, 0.45 * w0, stb[0][0] - x_fwd)
    c = math.sqrt(0.5)
    wp = (
        cq.Workplane("XY").workplane(offset=z0)
        .moveTo(x_fwd, -(w0 - r)).lineTo(x_fwd, w0 - r)
        .threePointArc((x_fwd + r - r * c, w0 - r + r * c), (x_fwd + r, w0))
    )
    path = [(stb[0][0], w0)] if stb[0][0] != x_fwd + r else []
    path += list(stb[1:]) + [(x, -y) for (x, y) in reversed(stb[:-1])]
    if stb[0][0] != x_fwd + r:
        path.append((stb[0][0], -w0))
    wp = wp.spline(path, includeCurrent=True)
    wp = wp.threePointArc((x_fwd + r - r * c, -(w0 - r + r * c)), (x_fwd, -(w0 - r)))
    return wp.close().extrude(z1 - z0)


def _coaming_slab(x_fwd: float, x_aft: float, z0: float, z1: float, n: int = 32):
    """Karmens ytre omriss som loddrett prisme: rett forkant med hjorne-
    radius COAMING_RAD, sider som foelger coaming_half_width, rett akterkant
    (den ligger nede i dekket)."""
    r = P.COAMING_RAD
    w0 = coaming_half_width(x_fwd + r)
    c = math.sqrt(0.5)
    xs = [x_fwd + r + (x_aft - x_fwd - r) * i / n for i in range(n + 1)]
    stb = [(x, coaming_half_width(x)) for x in xs]
    stb[0] = (stb[0][0], w0)
    wp = (
        cq.Workplane("XY").workplane(offset=z0)
        .moveTo(x_fwd, -(w0 - r)).lineTo(x_fwd, w0 - r)
        .threePointArc((x_fwd + r - r * c, w0 - r + r * c), (x_fwd + r, w0))
        .spline(stb[1:], includeCurrent=True)
        .lineTo(x_aft, -stb[-1][1])
        .spline([(x, -y) for (x, y) in reversed(stb[:-1])], includeCurrent=True)
        .threePointArc((x_fwd + r - r * c, -(w0 - r + r * c)), (x_fwd, -(w0 - r)))
    )
    return wp.close().extrude(z1 - z0)


def coaming_block() -> cq.Workplane:
    """Cockpitkarm med fallende overkant, fra litt foran bronnen til den
    gaar i ett med dekket (COAMING_X1). Bygges som et baand rundt bronnen
    (karmen minus bronnen, COAMING_GAP videre), saa begge overkantene kan
    rundes med fillet paa den frie delen. Unioneres foer bronnen skjaeres ut."""
    x0 = P.COCKPIT_X0 - P.COAMING_FWD
    z0 = min(C.sheer_z(x) for x in (x0, P.COAMING_X1)) - 220.0
    z1 = max(coaming_top_z(x) for x in (x0, P.COAMING_X1)) + 60.0
    slab = _coaming_slab(x0, P.COAMING_X1, z0, z1)
    top = _roof_body(x0 - 300.0, P.COAMING_X1 + 300.0, coaming_top_z, 1500.0, 2000.0,
                     camber=0.0, steps=40)
    g = P.COAMING_GAP
    hole = _plan_prism_well(_cockpit_stb(g), P.COCKPIT_X0 - g, P.COCKPIT_RAD + g,
                            z0 - 50.0, z1 + 50.0)
    ring = slab.intersect(top).cut(hole)
    return _try_fillet(ring, ring.faces(">Z").edges(), P.COAMING_EDGE_R)


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
    z1 = coaming_top_z(P.COCKPIT_X0) + 200.0
    return _plan_prism_well(_cockpit_stb(grow), P.COCKPIT_X0 - grow, P.COCKPIT_RAD + grow,
                            cockpit_floor_z() - grow, z1)


def cockpit_cut() -> cq.Workplane:
    """Cockpitbronnen: rett forkant, sider som foelger dekkskanten og en
    rundet bakkant som foelger hekken. Skjaeres bare opp til karmtoppen under
    sprayhooden, saa uthenget blir staaende. Fra V10 trinn 7 skjaeres den bare
    ned til setehoeyden (COCKPIT_SEAT_Z): setene langs sidene, setet paa
    tvers akter og brodekket forut staar igjen som massive flater, og
    fotbronnen (footwell_cut) skjaeres ned til gulvet."""
    z0 = getattr(P, "COCKPIT_SEAT_Z", cockpit_floor_z())
    prism = _plan_prism_well(_cockpit_stb(0.0), P.COCKPIT_X0, P.COCKPIT_RAD, z0, 2600.0)
    top = _roof_body(P.COCKPIT_X0 - 300.0, P.LOA + 200.0, _cockpit_lid_z, 1500.0, 2600.0, camber=0.0)
    return prism.intersect(top)


def footwell_cut() -> cq.Workplane:
    """Fotbronnen mellom setene (V10 trinn 7): rektangel med rundede hjoerner
    i plan fra FOOTWELL_X0 (brodekkets akterkant) til FOOTWELL_X1, loddrette
    vegger fra gulvet (COCKPIT_FLOOR_Z) og opp gjennom setehoeyden. Ingen
    overheng, saa den printes uten support."""
    x0, x1, w, r = P.FOOTWELL_X0, P.FOOTWELL_X1, P.FOOTWELL_HALF_W, P.FOOTWELL_RAD
    z0 = cockpit_floor_z()
    z1 = P.COCKPIT_SEAT_Z + 60.0
    b = (
        cq.Workplane("XY").workplane(offset=z0)
        .center(0.5 * (x0 + x1), 0.0)
        .rect(x1 - x0, 2.0 * w)
        .extrude(z1 - z0)
    )
    try:
        b = b.edges("|Z").fillet(r)
    except Exception:  # pragma: no cover
        pass
    return b
