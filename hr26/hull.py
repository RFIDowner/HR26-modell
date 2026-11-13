"""Skroget: loftet gjennom spant fra data/hull_stations.csv.

Spantene lukkes oppe av dekksbuen, slik at skroget kommer ut av loftet
med ferdig buet dekk - ingen ekstra boolsk operasjon som kan feile.
Hekken er rundet i plan; loften gaar forbi akterspeilet, og alt aktenfor
akterspeilets hellende, svakt buede flate kappes bort etterpaa.
"""
from __future__ import annotations

import math

import cadquery as cq
import numpy as np

from . import curves as C
from . import params as P

STERN_STATIONS = (7850.0, 7910.0)   # ekstra spant der hekken runder av
BOW_STATIONS = (4.0, 8.0)           # ekstra spant der dekkslinjen rundes av i nesen


def _section_wire(x: float, n_pts: int = 28) -> cq.Wire:
    """Lukket, speilsymmetrisk spant ved stasjon x, glatt rundt hele.

    Fem kanter: siden styrbord (kjol -> avrundet dekkskant), avrundingen,
    dekksbuen tvers over, avrundingen og siden babord. Kantene moetes med
    felles tangent, saa dekkskanten blir rund (C.section_parts) i stedet
    for en skarp knekk - en OCC-fillet paa den ferdige loften feiler der.

    Hver kant samples med de samme parameterverdiene og endetangentene ved
    alle stasjoner. Da faar splinene samme knutevektor, og loften blir en
    flate med faa knuter. Foer hadde hvert spant sine egne (over 1 000
    knuter paa tvers), og STL-en fikk lange, tynne trekanter.
    """
    sp = C.section_parts(x, n_side=max(n_pts, 28))
    side, corner, deck = sp["side"], sp["corner"], sp["deck"]
    ty, tz = sp["t_side"]
    dy, dz = sp["t_deck"]
    ps = [float(v) for v in sp["side_par"]]
    pc = [float(v) for v in sp["corner_par"]]
    pd = [float(v) for v in sp["deck_par"]]

    def spline(arr, par, t0, t1, sgn=1.0):
        # Parameterne er andeler av buelengden, saa farten langs kurven er
        # kurvens lengde: tangentene skaleres til den selv (scale=False).
        # OCCs egen skalering (scale=True) ga en cusp i styrbord sidespline.
        arr = np.asarray(arr, dtype=float)
        n = float(np.hypot(np.diff(arr[:, 0]), np.diff(arr[:, 1])).sum())
        v = [cq.Vector(x, sgn * float(y), float(z)) for y, z in arr]
        tg = [cq.Vector(0.0, t[0] * n, t[1] * n) for t in (t0, t1)]
        return cq.Edge.makeSpline(v, tangents=tg, parameters=list(par), scale=False)

    def rev(par):
        return [1.0 - v for v in reversed(par)]

    edges = [
        spline(side, ps, (1.0, 0.0), (ty, tz)),
        spline(corner, pc, (ty, tz), (dy, dz)),
        spline(deck, pd, (dy, dz), (dy, -dz)),
        spline(corner[::-1], rev(pc), (dy, -dz), (ty, -tz), -1.0),
        spline(side[::-1], rev(ps), (ty, -tz), (1.0, 0.0), -1.0),
    ]
    return cq.Wire.assembleEdges(edges)


def transom_cutter(offset: float = 0.0) -> cq.Workplane:
    """Alt aktenfor akterspeilet.

    Akterspeilet heller TRANSOM_RAKE med toppen akterover og er svakt buet i
    plan (TRANSOM_CAMBER_R). Kuttet av skroget (offset = 0) runder ogsaa
    hjoernene mot skrogsidene (_rounded_cutter). `offset` flytter flaten saa
    mange mm akterover (navnet i relieff) og gir det enkle prismet.
    """
    if offset == 0.0 and P.TRANSOM_CORNER_L > 0.0:
        try:
            return _rounded_cutter()
        except Exception as exc:  # pragma: no cover - faller tilbake til skarpe hjoerner
            print(f"  advarsel: rundede akterspeilhjoerner feilet ({exc}); bruker skarpe")
    return _plain_cutter(offset)


def _plain_cutter(offset: float = 0.0) -> cq.Workplane:
    """Et prisme med buet forkant (akterspeilets kamber i plan), dreid om en
    tverrgaaende akse i DWL saa flaten heller som akterspeilet."""
    R = P.TRANSOM_CAMBER_R
    xw = P.TRANSOM_WL_X + offset
    half = 2400.0
    sag = R - math.sqrt(R * R - half * half)
    prism = (
        cq.Workplane("XY")
        .workplane(offset=-4000.0)
        .moveTo(xw - sag, -half)
        .threePointArc((xw, 0.0), (xw - sag, half))
        .lineTo(xw + 3000.0, half)
        .lineTo(xw + 3000.0, -half)
        .close()
        .extrude(8000.0)
    )
    ang = math.degrees(math.atan(P.TRANSOM_RAKE))
    return prism.rotate((xw, 0.0, 0.0), (xw, 1.0, 0.0), ang)


def hull_solid(n_stations: int = 34, n_pts: int = 28) -> cq.Solid:
    """Skroget som et lukket volum, uten kjol og ror, kappet av akterspeilet."""
    xs = C.stations(n_stations)
    # unnga degenererte spant helt i endene; tettere spant i nesen, der
    # dekkslinjen rundes av, og rundt hekken
    xs = [x for x in xs if 10.0 < x < P.LOA - 4.0]
    xs = sorted(set(list(BOW_STATIONS) + xs + list(STERN_STATIONS) + [P.LOA - 2.0]))
    xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 3.0]

    wires = [_section_wire(x, n_pts) for x in xs]
    loft = cq.Solid.makeLoft(wires, ruled=False)
    cut = cq.Workplane("XY").newObject([loft]).cut(transom_cutter())
    solids = cut.val().Solids()
    if len(solids) != 1:
        raise RuntimeError(f"akterspeilkuttet ga {len(solids)} solider")
    return solids[0]


def hull(n_stations: int = 34) -> cq.Workplane:
    """Skrog kappet ved dekkskanten, med baug og hekk lukket."""
    s = hull_solid(n_stations)
    return cq.Workplane("XY").newObject([s])


# ------------------------------------------------------------- fenderlist
def _side_frame(x: float, zc: float):
    """Skrogsidens halvbredde ved stasjon x i hoyden zc, og sidens normal
    utover i spantets plan (ny, nz)."""
    sec = np.array(C.section(x, 60))
    zz = np.maximum.accumulate(sec[:, 1])
    yc = float(np.interp(zc, zz, sec[:, 0]))
    y_lo = float(np.interp(zc - 25.0, zz, sec[:, 0]))
    y_hi = float(np.interp(zc + 25.0, zz, sec[:, 0]))
    ty, tz = y_hi - y_lo, 50.0                 # tangent oppover langs siden
    L = math.hypot(ty, tz)
    return yc, (tz / L, -ty / L)


def _smooth(v: np.ndarray, sigma: int) -> np.ndarray:
    """Gauss-glatting av jevnt samplede verdier; endene speiles (odde), saa
    endepunktene og retningen der beholdes."""
    if sigma < 1 or len(v) < 3:
        return v
    k = np.arange(-3 * sigma, 3 * sigma + 1)
    w = np.exp(-0.5 * (k / sigma) ** 2)
    w /= w.sum()
    h = min(3 * sigma, len(v) - 1)
    pad = np.concatenate([2 * v[0] - v[h:0:-1], v, 2 * v[-1] - v[-2:-h - 2:-1]])
    out = np.convolve(pad, w, "same")[h:h + len(v)]
    if 3 * sigma > h:              # for kort til full kjerne: behold uglattet
        return v
    return out


def _hermite(p0, t0, p1, t1, n):
    """Kubisk Hermite-kurve fra p0 (retning t0) til p1 (retning t1)."""
    L = float(np.linalg.norm(p1 - p0))
    s = np.linspace(0.0, 1.0, n)[:, None]
    h00 = 2 * s ** 3 - 3 * s ** 2 + 1
    h10 = s ** 3 - 2 * s ** 2 + s
    h01 = -2 * s ** 3 + 3 * s ** 2
    h11 = s ** 3 - s ** 2
    return h00 * p0 + h10 * L * t0 + h01 * p1 + h11 * L * t1


def _strake_path(step: float = 20.0):
    """Listens senterlinje paa styrbord side som tette punkter, med skrogets
    normal utover: (pts (n,3), nrm (n,3)). Fra STRAKE_X0 langs skrogsiden i
    hoyden strake_z, rundt hekkens rundede hjoerne (samme bue som kuttet i
    transom_cutter) og tvers over akterspeilet til senterlinjen.

    Siden glattes lett (Gauss, ca. 40 mm), og knekken der hjoernebuen moeter
    siden (TRANSOM_CORNER_EXIT) jevnes ut med en kort overgangskurve - listen
    ligger hoyst et par mm fra skrogsiden der, og baksiden er begravd."""
    def inside(x):
        zc = C.strake_z(x)
        yc, _ = _side_frame(x, zc)
        return x < C.transom_x(zc, yc)

    # der siden treffer akterspeilet i listens hoyde (halvering)
    lo, hi = P.STRAKE_X0, P.LOA - 2.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if inside(mid):
            lo = mid
        else:
            hi = mid
    zs = C.strake_z(lo)

    # hekkens omriss i listens hoyde: hjoernebuen og akterspeilet
    K = _corner(zs)
    plan = _stern_plan(zs) if P.TRANSOM_CORNER_L > 0.0 else None
    if plan is None or K is None or plan[0] >= K[1] - 1.0:
        yt, R, a = (K[1] if K is not None else 0.0), 1.0, 0.0     # skarpt hjoerne
    else:
        yt, R, a = plan
    (ex, ey), _pe = _arc_point(zs, yt, R, a)

    # siden: tette punkter, glattet
    xs = np.arange(P.STRAKE_X0, ex - 1.0, step)
    side = np.array([[x, _side_y(x, C.strake_z(x)), C.strake_z(x)] for x in xs])
    side[:, 1] = _smooth(side[:, 1], int(round(40.0 / step)))
    side[:, 2] = _smooth(side[:, 2], int(round(40.0 / step)))
    nz_side = np.array([_side_frame(x, z)[1][1] for x, _, z in side])

    # buen (fra siden mot akterspeilet) og akterspeilet til senterlinjen
    n_arc = int(math.ceil(R * a / 15.0))
    if n_arc < 2:
        n_arc, arc = 0, np.array([[ex, ey]])
    else:
        arc = np.array([_arc_point(zs, yt, R, a * (1.0 - i / n_arc))[0] for i in range(n_arc + 1)])
    n_tr = max(4, int(math.ceil(yt / step)))
    ys = yt * (1.0 - np.arange(1, n_tr + 1) / n_tr)
    # over akterspeilet buer listen opp mot midten (IMG_9391); loeftet er 0
    # med vannrett tangent der hjoernebuen moeter akterspeilet
    zt = zs + P.STRAKE_TRANSOM_RISE * (1.0 - (ys / yt) ** 2) ** 2
    tr = np.array([[C.transom_x(z, y), y, z] for y, z in zip(ys, zt)])
    stern = np.vstack([np.c_[arc, np.full(len(arc), zs)], tr])

    # overgang: kutt siden og buen 50 mm fra knekken, bind sammen med Hermite
    s_st = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(stern, axis=0), axis=1))]
    j = int(np.searchsorted(s_st, min(50.0, 0.5 * s_st[-1])))
    i = int(np.searchsorted(side[:, 0], ex - 50.0))
    i = max(i, 2)
    t0 = side[i - 1] - side[i - 2]
    t1 = stern[j + 1] - stern[j]
    blend = _hermite(side[i - 1], t0 / np.linalg.norm(t0), stern[j], t1 / np.linalg.norm(t1), 8)
    pts = np.vstack([side[:i - 1], blend, stern[j + 1:]])
    n_side = i - 1

    # normal: vinkelrett paa banen i plan, helning fra spantet paa siden og
    # fra akterspeilets helning paa akterspeilet (lineaert fram til buens
    # tangeringspunkt paa akterspeilet)
    d = np.gradient(pts[:, :2], axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    nplan = np.c_[-d[:, 1], d[:, 0]]
    nz_tr = -math.sin(math.atan(P.TRANSOM_RAKE))
    kp = min(n_side + len(blend) - 1 + max(0, n_arc - j), len(pts) - 1)   # buens ende paa akterspeilet
    nz = np.full(len(pts), nz_tr)
    nz[:n_side] = nz_side[:n_side]
    nz[n_side:kp + 1] = np.linspace(nz_side[n_side - 1], nz_tr, kp + 1 - n_side)
    nrm = np.c_[nplan * np.sqrt(1.0 - nz ** 2)[:, None], nz]
    pts[-1, 1] = 0.0
    return pts, nrm


def _strake_profile():
    """Listens tverrsnitt som lukket kurve i (n, u): n utover fra skrogsiden,
    u oppover langs den, 0 paa listens senterlinje. Toppen er en kvartsirkel,
    ytterkanten rund, og undersiden en kvart-ellipse som ender i 45 grader mot
    skroget. Baksiden ligger STRAKE_BURY inne i skroget."""
    Pn, H, B = P.STRAKE_PROUD, P.STRAKE_H, P.STRAKE_BURY
    s = max(H - Pn, 1.05 * Pn)
    a_b = math.sqrt(s * s - Pn * Pn)
    f45 = math.atan2(a_b, Pn)
    uc = 0.5 * (s - Pn)                   # ytterpunktet; synlig fra uc - s til uc + Pn
    u_top, u_bot = uc + Pn, uc - s
    n1, u1 = Pn * math.cos(f45), uc - a_b * math.sin(f45)
    vis = [(0.0, u_bot), (0.5 * n1, u_bot + 0.5 * n1)]
    vis += [(Pn * math.cos(f), uc - a_b * math.sin(f)) for f in np.linspace(f45, 0.0, 5)]
    vis += [(Pn * math.cos(f), uc + Pn * math.sin(f)) for f in np.linspace(0.0, 0.5 * math.pi, 6)[1:]]
    back = [(-0.35 * B, u_top - 1.0), (-0.75 * B, u_top - 6.0), (-B, u_top - 18.0),
            (-B, 0.0), (-B, u_bot + 4.0), (-0.75 * B, u_bot - 7.0),
            (-0.35 * B, u_bot - 7.0), (-0.12 * B, u_bot - 3.6)]
    return vis + back


def _frames(pts, nrm):
    """Ortonormale rammer (t, n, u) langs banen."""
    t = np.gradient(pts, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    n = nrm - np.sum(nrm * t, axis=1, keepdims=True) * t
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    u = np.cross(n, t)            # oppover naar banen gaar babord -> akter -> styrbord
    return t, n, u


def rubbing_strake(n_stations: int = 48) -> cq.Workplane:
    """Fenderlist: en slank, avrundet list langs skrogsiden og rundt hekken.

    Glatt loft (ikke ruled) gjennom like tverrsnitt (_strake_profile) med
    STRAKE_STEP mellomrom, staaende vinkelrett paa listens senterlinje og
    dreid etter skrogets normal der. Ett sammenhengende volum fra babord
    forende, rundt akterspeilet, til styrbord forende. I forendene dykker
    listen jevnt inn i skroget (STRAKE_TAPER), saa den slutter uten endeflate.
    (`n_stations` brukes ikke lenger, men beholdes for kallene.)
    """
    pts, nrm = _strake_path()
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    # jevnt fordelte tverrsnitt (ujevn avstand faar loften til aa slaa ut)
    n = max(2, int(round(s[-1] / P.STRAKE_STEP)))
    sk = np.linspace(0.0, s[-1], n + 1)
    fp = np.c_[[np.interp(sk, s, pts[:, i]) for i in range(3)]].T
    fn = np.c_[[np.interp(sk, s, nrm[:, i]) for i in range(3)]].T
    fp[-1, 1] = 0.0
    # forenden dykker inn i skroget
    w = np.clip(sk / P.STRAKE_TAPER, 0.0, 1.0)
    dive = (P.STRAKE_PROUD + 4.0) * (1.0 - w * w * (3.0 - 2.0 * w))

    # babord forende -> akterspeilet -> styrbord forende (senterlinjen en gang)
    mir = np.array([1.0, -1.0, 1.0])
    allp = np.vstack([fp * mir, fp[-2::-1]])
    alln = np.vstack([fn * mir, fn[-2::-1]])
    alld = np.r_[dive, dive[-2::-1]]
    t, nv, uv = _frames(allp, alln)

    prof = _strake_profile()
    m = len(prof)
    par = list(np.linspace(0.0, 1.0, m + 1))
    wires = []
    for c, d, nn, uu in zip(allp, alld, nv, uv):
        c = c - d * nn
        v = [cq.Vector(*(c + pn * nn + pu * uu)) for pn, pu in prof]
        wires.append(cq.Wire.assembleEdges([cq.Edge.makeSpline(v, periodic=True, parameters=par)]))
    return cq.Workplane("XY").newObject([_loft3(wires)])


def _loft3(wires) -> cq.Solid:
    """Glatt loft gjennom wirene med hoyst tredjegrads flate paa tvers av
    snittene. Standardloften (opptil grad 8) svinger mellom mange snitt og
    ga selvkryssende flater for fenderlisten og et ugyldig akterspeilkutt."""
    from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections

    b = BRepOffsetAPI_ThruSections(True, False, 1e-6)
    b.SetMaxDegree(3)
    for w in wires:
        b.AddWire(w.wrapped)
    b.Build()
    return cq.Solid(b.Shape())


# ------------------------------------------------- akterspeilets hjoerner
# OCC klarer ikke aa runde kantene mellom akterspeilet og skrogsidene med
# fillet (V10-analysen), saa avrundingen bygges inn i kuttet: i hvert
# vannrette snitt gaar kuttets forkant langs akterspeilet og svinger saa
# forover i en bue som moeter skrogsiden med en liten restknekk. Kuttet
# loftes gjennom slike snitt og faar en eneste glatt forkant, og det
# skjaerer skrogsiden overalt med en tydelig vinkel - ingen tangerende
# flater som kan faa det boolske kuttet til aa feile. Formen regnes ut av
# kurve-API-et (C.section), saa den foelger med naar spantene endres.

_CUT_FAR_X = 8400.0           # kuttet gaar saa langt akter
_CUT_FAR_Y = 1400.0           # og saa langt ut til sidene
_CUT_LEVELS = (-450.0, 1150.0, 50.0)   # vannrette snitt: fra, til, steg (under bunnen
                                        # og over dekket i hekken)
_CUT_PARK_Y = 450.0           # der det ikke rundes, tangerer buen akterspeilet her (utenfor skroget)
_CUT_RUN = 80.0               # forkanten fortsetter saa langt rett ut forbi buen


def _side_y(x: float, z: float) -> float:
    """Skrogsidens halvbredde ved (x, z) etter det analytiske spantet. 0 under
    bunnen; over dekkskanten dekkskantens halvbredde (dekkets omriss)."""
    sec = np.asarray(C.section(x, 60), dtype=float)
    zz = np.maximum.accumulate(sec[:, 1])
    if z <= zz[0]:
        return 0.0
    if z >= zz[-1]:
        return float(sec[-1, 0])
    return float(np.interp(z, zz, sec[:, 0]))


def _side_psi(x: float, z: float, h: float = 25.0) -> float:
    """Retningen langs skrogsiden forover ved (x, z), vinkel i plan."""
    dy = (_side_y(x - h, z) - _side_y(x + h, z)) / (2.0 * h)
    return math.atan2(dy, -1.0)


def _transom_psi(y: float) -> float:
    """Retningen langs akterspeilet utover ved halvbredde y, vinkel i plan."""
    R = P.TRANSOM_CAMBER_R
    k = math.sqrt(1.0 + P.TRANSOM_RAKE ** 2)
    return math.atan2(1.0, -k * y / math.sqrt(R * R - y * y))


def _arc_point(z: float, yt: float, R: float, a: float):
    """Punkt (x, y) og retning paa buen med radius R som tangerer akterspeilet
    i halvbredde yt (hoyde z), etter at den har svingt vinkelen a forover."""
    x0 = C.transom_x(z, yt)
    p0 = _transom_psi(yt)
    p = p0 + a
    return (x0 + R * (math.sin(p) - math.sin(p0)), yt + R * (math.cos(p0) - math.cos(p))), p


def _corner(z: float):
    """Hjoernet (x, y) der skrogsiden moeter akterspeilet i hoyden z, eller None."""
    if _side_y(C.transom_x(z, 0.0), z) <= 1.0:
        return None
    lo, hi = 0.0, 1500.0
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if _side_y(C.transom_x(z, m), z) > m:
            lo = m
        else:
            hi = m
    y = 0.5 * (lo + hi)
    return C.transom_x(z, y), y


def _corner_arc(z: float):
    """Hjoernebuen i hoyden z med full avrunding: (yt, R, a), eller None.

    R velges saa buen tangerer akterspeilet ca. TRANSOM_CORNER_L fra
    hjoernet (hoyst 5 x den). Buen svinger hjoernevinkelen minus
    restknekken TRANSOM_CORNER_EXIT (som er hoyst halve hjoernevinkelen),
    og yt finnes ved halvering slik at buens ende ligger paa siden. Siden
    krummer samme vei som buen, saa den moeter siden med minst restknekken -
    aldri tangerende."""
    K = _corner(z)
    if K is None:
        return None
    th = _side_psi(K[0] - 1.0, z) - _transom_psi(K[1])
    if th < math.radians(2.0):
        return None
    ex = min(math.radians(P.TRANSOM_CORNER_EXIT), 0.5 * th)
    R = min(P.TRANSOM_CORNER_L / math.tan(0.5 * th), 5.0 * P.TRANSOM_CORNER_L)
    a = th - ex

    def miss(yt):
        (ex_, ey), _p = _arc_point(z, yt, R, a)
        return _side_y(ex_, z) - ey

    lo, hi = 0.0, K[1]
    if miss(lo) <= 0.0:
        return None
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if miss(m) > 0.0:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi), R, a


def _smoothstep(e0: float, e1: float, v: float) -> float:
    t = min(max((v - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


_PLAN_CACHE: dict = {}


def _stern_plans():
    """(z, yt, R, a) for alle snittene i kuttet.

    Under vannlinjen trappes rundingen ned: buen flyttes jevnt ut til den
    ligger like utenfor hjoernet (der skjaerer bare akterspeilet, som foer).
    Like under dekkskanten fryses buen, og snittene over er samme form
    forskjoevet med akterspeilets helning - over dekkskanten finnes ingen
    skrogside aa regne hjoernet fra. Snitt uten skrog bruker nabosnittets
    form. Alt varierer jevnt med z, ellers slaar loften ut."""
    key = (P.TRANSOM_CORNER_L, P.TRANSOM_CORNER_EXIT, P.TRANSOM_CORNER_Z, _CUT_LEVELS)
    if key in _PLAN_CACHE:
        return _PLAN_CACHE[key]
    z0, z1, dz = _CUT_LEVELS
    zs = np.arange(z0, z1 + 0.5 * dz, dz)
    K = _corner(P.TRANSOM_CORNER_Z[1])
    z_top = C.sheer_z(K[0]) - 30.0 if K is not None else 900.0
    top = _corner_arc(z_top)
    while top is None and z_top > P.TRANSOM_CORNER_Z[1]:
        z_top -= 10.0
        top = _corner_arc(z_top)
    if top is None:
        raise RuntimeError("fant ingen hjoernebue under dekkskanten")
    rows = []                         # (z, yt, R, a); None der det ikke er noen bue
    for z in zs:
        z = float(z)
        arc = top if z >= z_top else _corner_arc(z)
        rows.append((z, *(arc if arc is not None else (None, None, None))))
    ok = [i for i, r in enumerate(rows) if r[1] is not None]
    if not ok:
        raise RuntimeError("fant ingen hjoernebue")
    tab = []
    for i, (z, yt, R, a) in enumerate(rows):
        j = min(ok, key=lambda k: abs(k - i))
        yt, R, a = rows[j][1], rows[j][2], rows[j][3]
        w = 1.0 - _smoothstep(P.TRANSOM_CORNER_Z[0], P.TRANSOM_CORNER_Z[1], z)
        K = _corner(z)
        if K is not None and K[1] + 30.0 > _CUT_PARK_Y and w > 0.0:
            raise RuntimeError("hjoernet ligger utenfor parkeringen ved z = %.0f" % z)
        tab.append((z, (1.0 - w) * yt + w * _CUT_PARK_Y, R, a))
    # lett glatting i z (spantenes knekker gir smaa sprang fra snitt til snitt)
    arr = np.array(tab)
    for k in (1, 2, 3):
        v = arr[:, k].copy()
        for _ in range(2):
            v[1:-1] = 0.25 * v[:-2] + 0.5 * v[1:-1] + 0.25 * v[2:]
        arr[:, k] = v
    out = [tuple(float(c) for c in r) for r in arr]
    _PLAN_CACHE[key] = out
    return out


def _stern_plan(z: float):
    """Hjoernebuen (yt, R, a) i hoyden z, interpolert mellom kuttets snitt."""
    pl = np.array(_stern_plans())
    if z < pl[0, 0] or z > pl[-1, 0]:
        return None
    return tuple(float(np.interp(z, pl[:, 0], pl[:, k])) for k in (1, 2, 3))


def _cutter_wire(z: float, yt: float, R: float, a: float, n_arc: int = 8, n_tr: int = 10):
    """Lukket, vannrett wire for kuttet i hoyden z: forkanten (en spline fra
    styrbord til babord: rett stykke, bue, akterspeil, bue, rett stykke) og
    tre rette linjer rundt utenfor skroget."""
    E, pe = _arc_point(z, yt, R, a)
    run = [(E[0] + f * _CUT_RUN * math.cos(pe), E[1] + f * _CUT_RUN * math.sin(pe)) for f in (1.0, 0.5)]
    arc = [_arc_point(z, yt, R, a * (1.0 - i / n_arc))[0] for i in range(n_arc + 1)]
    tr = [(C.transom_x(z, y), y) for y in (yt * (1.0 - np.arange(1, n_tr + 1) / n_tr))]
    stb = run + arc + tr                       # Q -> E -> P_t -> senterlinjen
    port = [(x, -y) for (x, y) in reversed(stb[:-1])]
    pts = [cq.Vector(x, y, z) for (x, y) in stb + port]
    # faste parametre (samme i alle snitt), saa loften blir ryddig
    seg = [0.5 * _CUT_RUN] * 2 + [220.0 / n_arc] * n_arc + [600.0 / n_tr] * n_tr
    seg = seg + seg[::-1]
    par = np.r_[0.0, np.cumsum(seg)]
    par = list(par / par[-1])
    front = cq.Edge.makeSpline(pts, parameters=par)
    q_s, q_p = pts[0], pts[-1]
    f_p = cq.Vector(_CUT_FAR_X, -_CUT_FAR_Y, z)
    f_s = cq.Vector(_CUT_FAR_X, _CUT_FAR_Y, z)
    return cq.Wire.assembleEdges([front, cq.Edge.makeLine(q_p, f_p),
                                  cq.Edge.makeLine(f_p, f_s), cq.Edge.makeLine(f_s, q_s)])


def _rounded_cutter() -> cq.Workplane:
    """Kuttet med rundede hjoerner: loft gjennom vannrette snitt (se over).

    Loften lages med hoyst tredjegrads flater i hoyderetningen (_loft3)."""
    wires = [_cutter_wire(z, yt, R, a) for (z, yt, R, a) in _stern_plans()]
    solid = _loft3(wires)
    if not solid.isValid() or solid.Volume() <= 0.0:
        raise RuntimeError("ugyldig kutt")
    return cq.Workplane("XY").newObject([solid])


# ---------------------------------------------- akterspeilets overkant
# OCC-fillet feiler ogsaa paa kanten mellom akterspeilet og dekket, saa den
# rundes med et eget kutt: i hvert loddrette snitt (y fast) en sirkelbue som
# skjaerer dekket og akterspeilet med en liten restknekk (TRANSOM_TOP_EXIT) i
# stedet for aa tangere dem - tangerende flater faar det boolske kuttet til
# aa feile. Snittene loftes paa tvers. Mot hjoernene (der akterspeilet runder
# over i skrogsiden) avtar radien jevnt.

def _top_edge(y: float):
    """Akterspeilets overkant ved halvbredde y: (x, z)."""
    z = C.deck_z(C.transom_x(950.0, y), y)
    x = C.transom_x(z, y)
    for _ in range(30):
        x = C.transom_x(z, y)
        z1 = C.deck_z(x, y)
        if abs(z1 - z) < 1e-4:
            break
        z = z1
    return x, z


def _top_profile(y: float, R: float, out: float = 40.0):
    """Kuttets tverrsnitt i planet y = konstant: liste av (x, z) og
    buens midtpunkt. Hjoernet E, dekket forover langs a, akterspeilet
    nedover langs b."""
    xe, ze = _top_edge(y)
    h = 2.0
    a = np.array([-h, C.deck_z(xe - h, y) - C.deck_z(xe, y)])
    a /= np.linalg.norm(a)
    b = np.array([-P.TRANSOM_RAKE, -1.0])
    b /= np.linalg.norm(b)
    E = np.array([xe, ze])
    phi = math.acos(float(np.clip(a @ b, -1.0, 1.0)))
    u = (a + b) / np.linalg.norm(a + b)              # halveringslinjen, inn i skroget
    d = R * math.cos(math.radians(P.TRANSOM_TOP_EXIT)) / math.sin(0.5 * phi)
    Cc = E + d * u

    def near_hit(v):
        # E + t v paa sirkelen |p - Cc| = R, naermeste roten til E
        w = E - Cc
        bq = 2.0 * (v @ w)
        cq_ = w @ w - R * R
        disc = max(bq * bq - 4.0 * cq_, 0.0)
        return E + 0.5 * (-bq - math.sqrt(disc)) * v

    IA, IB = near_hit(a), near_hit(b)
    M = Cc - R * u
    nA = np.array([-a[1], a[0]])
    if nA @ (-u) < 0.0:
        nA = -nA
    nB = np.array([-b[1], b[0]])
    if nB @ (-u) < 0.0:
        nB = -nB
    return [IA, M, IB, IB + out * nB, E - out * u, IA + out * nA]


def round_transom_top(w: cq.Workplane) -> cq.Workplane:
    """Runder akterspeilets overkant paa et ferdig skrog. Maa gjoeres ETTER
    at fenderlisten er unionert: gjort i hull_solid fikk det unionen med
    listen til aa miste listen (V10, samlet bygg)."""
    if P.TRANSOM_TOP_R <= 0.0:
        return w
    try:
        out = w.cut(transom_top_cutter())
        if len(out.val().Solids()) == 1 and out.val().isValid():
            return out
        print("  advarsel: avrundingen av akterspeilets overkant ga et ugyldig volum; hopper over")
    except Exception as exc:  # pragma: no cover
        print(f"  advarsel: avrundingen av akterspeilets overkant feilet ({exc}); hopper over")
    return w


def transom_top_cutter(n: int = 21) -> cq.Workplane:
    """Kuttet som runder akterspeilets overkant (se over)."""
    y_end = None
    # overkanten gaar ut til der dekkskantens avrunding begynner
    for y in np.arange(300.0, 900.0, 5.0):
        x, _z = _top_edge(float(y))
        if C.deck_half_breadth(x) - P.DECK_EDGE_R - 10.0 < y:
            y_end = float(y) - 5.0
            break
    if y_end is None:
        raise RuntimeError("fant ikke enden av akterspeilets overkant")
    ys = np.linspace(-y_end, y_end, n)
    wires = []
    for y in ys:
        t = min(max((y_end - abs(y)) / P.TRANSOM_TOP_TAPER, 0.0), 1.0)
        R = max(P.TRANSOM_TOP_R * t * t * (3.0 - 2.0 * t), 1.5)
        IA, M, IB, Q2, Q0, Q1 = _top_profile(float(y), R)
        v = lambda p: cq.Vector(float(p[0]), float(y), float(p[1]))
        arc = cq.Edge.makeThreePointArc(v(IA), v(M), v(IB))
        edges = [arc, cq.Edge.makeLine(v(IB), v(Q2)), cq.Edge.makeLine(v(Q2), v(Q0)),
                 cq.Edge.makeLine(v(Q0), v(Q1)), cq.Edge.makeLine(v(Q1), v(IA))]
        wires.append(cq.Wire.assembleEdges(edges))
    # Rett (ruled) loft mellom snittene: den glatte loften gjennom alle
    # snittene ga et kutt som OCC ikke klarte aa trekke fra (hjoernet ble
    # staaende). Avstanden mellom snittene er ca. 55 mm og overkanten er
    # svakt buet i plan, saa fasettene avviker under 0,2 mm.
    solid = cq.Solid.makeLoft(wires, ruled=True)
    if not solid.isValid():
        raise RuntimeError("ugyldig kutt for overkanten")
    return cq.Workplane("XY").newObject([solid])
