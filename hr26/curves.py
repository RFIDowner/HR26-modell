"""Fairede lengdekurver for skroget.

Kurvene er tilpasset maalepunktene fra profil- og dekksplantegningen i 1:50
fra HR 26-brosjyren. Alle verdier i fullskala mm: x maalt fra baugen og
akterover, z fra konstruksjonsvannlinjen (DWL), y halvbredde.

Hver lengdekurve er EN kubisk B-spline, tilpasset maalepunktene med minste
kvadraters metode. Foer V10 var kurvene rette streker mellom punktene
(np.interp, knekk i hvert punkt) glattet med glidende middel, som laget en
S-bue i baugen og trakk kurvene bort fra maalingene. Splinene har
kontinuerlig krumning og ligger innenfor en strektykkelse paa tegningen
(0,25 mm i 1:50 = 12,5 mm) av punktene:

  * dekkslinjen i plan: den sporede dekkslinjen (data/deck_halfbreadth.csv)
    fram til P.STERN_OUTLINE[0] og den punktvis maalte hekken
    (P.STERN_OUTLINE), i ett stykke uten skjoet. Den krummer samme vei hele
    veien (ingen S-bue), og stoerste bredde er P.BEAM.
  * springet (dekkskanten): utjevnende spline gjennom P.DECK_EDGE_Z.
  * fenderlistens senterlinje: strake_z_mm i data/hull_stations.csv.
  * profilen paa senterlinjen: forstevnen over vann, den sporede forfoten og
    kanobunnen (data/uw_station.csv) og P.CANOE_BOTTOM_HIDDEN der kjolen,
    propellen og roret skjuler bunnen - ett stykke fra stevnhodet til hekken.

Splinene er skrevet i ren numpy (de Boors algoritme), saa scipy trengs ikke.
"""
from __future__ import annotations

import bisect
import csv
import math
import os

import numpy as np

from . import params as P

_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))


# ------------------------------------------------------------- B-spline
class _Spline:
    """Kubisk B-spline med knuter t og koeffisienter c, evaluert med de
    Boors algoritme. Utenfor [t[3], t[-4]] holdes endeverdien."""

    def __init__(self, t, c, k: int = 3):
        self.t = [float(v) for v in t]
        self.c = [float(v) for v in c]
        self.k = k
        self.x0, self.x1 = self.t[k], self.t[-k - 1]

    def __call__(self, x: float) -> float:
        t, k = self.t, self.k
        x = min(max(float(x), self.x0), self.x1)
        j = min(max(bisect.bisect_right(t, x) - 1, k), len(t) - k - 2)
        d = self.c[j - k:j + 1]
        for r in range(1, k + 1):
            for i in range(k, r - 1, -1):
                a = (x - t[i + j - k]) / (t[i + 1 + j - r] - t[i + j - k])
                d[i] = (1.0 - a) * d[i - 1] + a * d[i]
        return d[k]


def _basis(x, t, der: int = 0, k: int = 3):
    """B-spline-basisen (Cox-de Boor): en rad per x, en kolonne per
    basisfunksjon. der > 0 gir basisens deriverte."""
    t = np.asarray(t, dtype=float)
    x = np.clip(np.atleast_1d(np.asarray(x, dtype=float)), t[k], t[-k - 1])
    n = len(t) - 1
    B = np.zeros((len(x), n))
    for i in range(n):
        if t[i] < t[i + 1]:
            B[:, i] = (x >= t[i]) & (x < t[i + 1])
    last = max(i for i in range(n) if t[i] < t[i + 1])
    B[x >= t[last + 1], last] = 1.0
    for d in range(1, k + 1):
        Bn = np.zeros((len(x), n - d))
        for i in range(n - d):
            a, b = t[i + d] - t[i], t[i + d + 1] - t[i + 1]
            if d > k - der:
                fa = d / a if a > 0 else 0.0
                fb = d / b if b > 0 else 0.0
                Bn[:, i] = fa * B[:, i] - fb * B[:, i + 1]
            else:
                fa = (x - t[i]) / a if a > 0 else 0.0
                fb = (t[i + d + 1] - x) / b if b > 0 else 0.0
                Bn[:, i] = fa * B[:, i] + fb * B[:, i + 1]
        B = Bn
    return B


def _bending(t, k: int = 3):
    """Integralet av s''(x)^2 som kvadratisk form i koeffisientene (Gauss,
    eksakt for kubiske splines)."""
    gx, gw = np.polynomial.legendre.leggauss(k + 1)
    xs, ws = [], []
    for a, b in zip(t[:-1], t[1:]):
        if b > a:
            xs.append(0.5 * (b - a) * gx + 0.5 * (a + b))
            ws.append(0.5 * (b - a) * gw)
    D = _basis(np.concatenate(xs), t, 2, k)
    return D.T @ (D * np.concatenate(ws)[:, None])


def _fit(x, y, x0, x1, interior, w=None, lam=0.0, bend=0, eq=(), le=()):
    """Kubisk spline paa [x0, x1] tilpasset (x, y) med minste kvadrater.

    interior: indre knuter. w: vekt per punkt. lam: straff paa krumningen
    (integralet av s''^2), som i en utjevnende spline.
    bend = +1 krever s'' >= 0 overalt, -1 krever s'' <= 0: kurven krummer
    samme vei hele veien. s'' er lineaer mellom knutene, saa kravet i
    knutene gjelder hele kurven.
    eq: (x, verdi) kurven skal gaa gjennom. le: (x, verdi) kurven skal
    ligge paa eller under. Ulikhetene loeses med en aktiv-mengde-metode.
    """
    t = np.r_[[x0] * 4, np.asarray(interior, dtype=float), [x1] * 4]
    x = np.asarray(x, dtype=float)
    w = np.ones_like(x) if w is None else np.asarray(w, dtype=float)
    B = _basis(x, t)
    H = B.T @ (B * w[:, None])
    g = B.T @ (w * np.asarray(y, dtype=float))
    if lam:
        H = H + lam * _bending(t)
    n = H.shape[0]
    A = _basis([p[0] for p in eq], t) if eq else np.zeros((0, n))
    b = np.array([p[1] for p in eq], dtype=float)
    # ulikheter G c <= h
    G, h = np.zeros((0, n)), np.zeros(0)
    if bend:
        kn = np.unique(t)
        G, h = -bend * _basis(kn, t, 2), np.zeros(len(kn))
    if le:
        G = np.vstack([G, _basis([p[0] for p in le], t)])
        h = np.r_[h, [p[1] for p in le]]
    active: list[int] = []
    c = None
    for _ in range(len(h) + 50):
        M = np.vstack([A, G[active]])
        m = len(M)
        K = np.zeros((n + m, n + m))
        K[:n, :n] = H
        K[:n, n:] = M.T
        K[n:, :n] = M
        sol = np.linalg.solve(K, np.r_[g, b, h[active]])
        c, nu = sol[:n], sol[n + len(b):]
        # et aktivt krav som trekker feil vei slippes
        if active and nu.min() < -1e-9 * max(1.0, np.abs(nu).max()):
            active.pop(int(np.argmin(nu)))
            continue
        v = G @ c - h
        v[active] = -np.inf
        if len(v) == 0 or v.max() <= 1e-9 * max(1.0, np.abs(c).max()):
            break
        active.append(int(np.argmax(v)))
    return _Spline(t, c)


def _read(name, *cols):
    with open(os.path.join(_DIR, name), newline="") as fh:
        rows = list(csv.DictReader(fh))
    return [np.array([float(r[c]) for r in rows]) for c in cols]


# ------------------------------------------------------------- dekkslinje
# Indre knuter: jevnt langs skroget, tettere i hekkens runding (R ca. 290).
_DECK_KNOTS = (400, 800, 1600, 2400, 3200, 4000, 4800, 5600, 6400, 7000,
               7400, 7650, 7760, 7830)
_STERN_WEIGHT = 10.0    # hekkens punkter er maalt ett for ett, sporet er rastret


def _deck_spline():
    x, y = _read("deck_halfbreadth.csv", "x_from_bow_mm", "half_breadth_mm")
    so = np.array(P.STERN_OUTLINE)
    m = x < so[0, 0]
    xs, ys = np.r_[x[m], so[:, 0]], np.r_[y[m], so[:, 1]]
    w = np.r_[np.ones(int(m.sum())), np.full(len(so), _STERN_WEIGHT)]
    # stoerste bredde = BEAM (sporet gir 2 697, brosjyren 2 680)
    le = [(v, 0.5 * P.BEAM) for v in np.arange(0.0, so[-1, 0], 25.0)]
    return _fit(xs, ys, 0.0, so[-1, 0], _DECK_KNOTS, w, bend=-1, le=le)


_DECK = _deck_spline()
_DECK_X1 = P.STERN_OUTLINE[-1][0]


def _stern_table():
    """Dekkskantens halvbredde aktenfor akterspeilets hjoerne (siste punkt i
    P.STERN_OUTLINE): bredden holdes nesten (svakt fallende) fram forbi LOA.
    Loften gaar altsaa rett akterover forbi akterspeilet som et bredt
    stykke, og akterspeilets flate - med buen i plan - kappes ut av det
    etterpaa. Smalnet loften inn til en spiss der, ble den saa vridd at
    kuttet feilet."""
    y1 = _DECK(_DECK_X1)
    xs = [_DECK_X1, P.LOA + 20.0]
    ys = [y1, y1 - P.STERN_HOLD_SLOPE * (P.LOA + 20.0 - _DECK_X1)]
    return np.array(xs), np.array(ys)


_SX, _SY = _stern_table()


def deck_half_breadth(x: float) -> float:
    """Halvbredde ved dekkskanten.

    Splinen gaar fra baugen gjennom hekkens runding til akterspeilets
    hjoerne; aktenfor det holdes bredden, og akterspeilet kappes ut av
    loften (se _stern_table).
    """
    if x > _DECK_X1:
        return float(np.interp(x, _SX, _SY))
    return _DECK(x)


def transom_x(z: float, y: float = 0.0) -> float:
    """Akterspeilets x ved hoyde z og halvbredde y.

    Et plan som heller TRANSOM_RAKE (dx/dz) gjennom (TRANSOM_WL_X, 0), buet
    i plan med radius TRANSOM_CAMBER_R. Samme flate som hull.transom_cutter.
    """
    R = P.TRANSOM_CAMBER_R
    sag = R - np.sqrt(max(R * R - y * y, 0.0))
    return float(P.TRANSOM_WL_X + P.TRANSOM_RAKE * z - sag * np.sqrt(1.0 + P.TRANSOM_RAKE ** 2))


# ----------------------------------------------------- spring og fenderlist
def _sheer_spline():
    a = np.array(P.DECK_EDGE_Z)
    return _fit(a[:, 0], a[:, 1], a[0, 0], a[-1, 0], a[1:-1, 0], lam=P.SHEER_SMOOTHING)


_SHEER = _sheer_spline()

# Fenderlisten: rett i baugen, flater ut akter - krummer samme vei hele veien.
_STRAKE_KNOTS = (800, 1600, 2400, 3200, 4000, 4800, 5600, 6400, 7200)


def _strake_spline():
    x, z = _read("hull_stations.csv", "x_from_bow_mm", "strake_z_mm")
    return _fit(x, z, x[0], x[-1], _STRAKE_KNOTS, bend=+1)


_STRAKE = _strake_spline()


def sheer_z(x: float) -> float:
    """Dekkskantens hoyde over DWL (rekkas linje, over fenderlisten)."""
    return _SHEER(x)


def strake_z(x: float) -> float:
    """Fenderlistens senterlinje over DWL."""
    return _STRAKE(x)


# ------------------------------------------------- profil paa senterlinjen
# Forstevnen over vann er en rett linje (P.STEM_LINE) mellom hoydene
# P.STEM_LINE_Z; over den gaar splinen opp til stevnhodet (0, sheer_z(0)), og
# under den boeyer den jevnt inn i den sporede forfoten. Knutene ved 80/180
# og 450/750 lar boeyene ligge der de skal, saa linja er rett innen 1 mm.
_TRACE_X1 = 2800.0      # sporet kanobunn hit; aktenfor begynner kjolens rotkurve
_BOTTOM_KNOTS = (80, 180, 300, 450, 600, 750, 900, 1250, 1700, 2200, 2800, 3500,
                 4200, 5000, 5800, 6500, 7100, 7500, 7800)


def _bottom_spline():
    top = _SHEER(0.0)
    (x1, z1), (x2, z2) = P.STEM_LINE
    k = (x2 - x1) / (z2 - z1)
    sz = np.arange(P.STEM_LINE_Z[1], P.STEM_LINE_Z[0] - 1.0, -25.0)
    sx = x1 + k * (sz - z1)
    ux, ud = _read("uw_station.csv", "x_from_bow_mm", "depth_below_DWL_mm")
    m = (ux >= P.LWL_FWD) & (ux <= _TRACE_X1)
    tx, tz = ux[m][::6], -ud[m][::6]             # ca. 20 mm mellom punktene
    hid = np.array(P.CANOE_BOTTOM_HIDDEN)
    hx = np.arange(hid[0, 0], hid[-1, 0] + 1.0, 50.0)
    hz = np.interp(hx, hid[:, 0], hid[:, 1])
    hw = np.where(hx < P.KEEL_TE_ROOT, 0.15, 1.0)   # bak kjolen: bare en foering
    x = np.r_[sx, tx, hx]
    z = np.r_[sz, tz, hz]
    w = np.r_[np.ones(len(sx) + len(tx)), hw]
    x_root = 0.5 * (P.KEEL_LE_ROOT + P.KEEL_TE_ROOT)    # kjolroten (appendages.keel)
    eq = [(0.0, top), (P.LWL_FWD, 0.0),
          (x_root, float(np.interp(x_root, hid[:, 0], hid[:, 1])))]
    return _fit(x, z, 0.0, P.LOA, _BOTTOM_KNOTS, w, bend=+1, eq=eq)


_BOTTOM = _bottom_spline()


def bottom_z(x: float) -> float:
    """Kanobunnens hoyde over DWL (negativ under vann).

    Foran vannlinjens forkant er det forstevnen, opp til stevnhodet i
    dekkshoyde. Ett stykke fra stevnhodet til hekken, uten sprang i forfoten.
    V10 trinn 5: pluss en glatt rettelse fra bildene (P.BOTTOM_PHOTO_DZ).
    """
    if _BOTTOM_DZ is not None and _DZ_X0 < x < _DZ_X1:
        return _BOTTOM(x) + _BOTTOM_DZ(x)
    return _BOTTOM(x)


# ------------------------------------------------------- tverrsnittets form
# Hvert spant er EN glatt, konveks kurve fra kjolen (eller stevnen) til
# dekkskanten. Hjoernet mellom en bunnlinje gjennom kjolpunktet (helning
# P.SECTION_DEADRISE) og en sidelinje gjennom dekkskanten (utfall
# P.SECTION_FLARE) rundes av med en superellipse med eksponent P.SECTION_N:
#
#   P(th) = H - a (1 - sin(th)^(2/n)) ub + c (1 - cos(th)^(2/n)) us
#
# der H er hjoernet, ub og us bunn- og sideretningen og th fra 0 (kjolen)
# til pi/2 (dekkskanten). For n > 2 er kurven konveks, uten vendepunkt, og
# rett (null krumning) inn mot begge endene. Utfallet avtar oppover: buede
# sider og myk slag, slik bildene viser. Kjolpunktet (bottom_z), dekkskanten
# (deck_half_breadth, sheer_z) og fenderlistens hoyde ligger fast;
# vannlinjebredden blir et resultat av formen.
#
# Foer V10 var spantet to kurver limt sammen i DWL (superellipse under, hul
# potenskurve over), begge loddrette der: en knekk langs hele vannlinjen og
# hule sider. Vannlinjetabellene (WATERPLANE, WL_BEAM_FRACTION) hadde ingen
# kilde og er fjernet.


def _pchip(pairs):
    """Monoton kubisk interpolasjon (Fritsch-Carlson, som scipy PCHIP)
    gjennom tabellpunktene: glatt og uten oversving mellom punktene.
    Utenfor tabellen holdes endeverdien."""
    xs = [float(p[0]) for p in pairs]
    ys = [float(p[1]) for p in pairs]
    h = np.diff(xs)
    d = np.diff(ys) / h
    m = np.zeros(len(xs))
    for i in range(1, len(xs) - 1):
        if d[i - 1] * d[i] > 0.0:
            w1, w2 = 2.0 * h[i] + h[i - 1], h[i] + 2.0 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def end(h0, h1, d0, d1):
        v = ((2.0 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
        if np.sign(v) != np.sign(d0):
            return 0.0
        if np.sign(d0) != np.sign(d1) and abs(v) > 3.0 * abs(d0):
            return 3.0 * d0
        return v

    if len(xs) > 2:
        m[0] = end(h[0], h[1], d[0], d[1])
        m[-1] = end(h[-1], h[-2], d[-1], d[-2])
    else:
        m[:] = d[0]

    def f(t: float) -> float:
        if t <= xs[0]:
            return ys[0]
        if t >= xs[-1]:
            return ys[-1]
        i = min(bisect.bisect_right(xs, t) - 1, len(xs) - 2)
        s = (t - xs[i]) / h[i]
        return float((1 + 2 * s) * (1 - s) ** 2 * ys[i] + s * (1 - s) ** 2 * h[i] * m[i]
                     + s * s * (3 - 2 * s) * ys[i + 1] + s * s * (s - 1) * h[i] * m[i + 1])
    return f


# V10 trinn 5 (13.11 kveld): rettelse av senterlinjen fra IMG_9387 og IMG_9395
# (forfoten litt akterover, bunnen fra x 1,5 m jevnt dypere ned mot kjolen).
_DZ_TAB = getattr(P, "BOTTOM_PHOTO_DZ", None)
_BOTTOM_DZ = _pchip(_DZ_TAB) if _DZ_TAB else None
_DZ_X0, _DZ_X1 = (float(_DZ_TAB[0][0]), float(_DZ_TAB[-1][0])) if _DZ_TAB else (0.0, 0.0)
_FLARE = _pchip(P.SECTION_FLARE)
_NEXP = _pchip(P.SECTION_N)
_DEADRISE = _pchip(P.SECTION_DEADRISE)
_DEADWOOD = _pchip(getattr(P, "DEADWOOD_H", [(0.0, 0.0), (1.0, 0.0)]))
_DWW_TAB = getattr(P, "DEADWOOD_W", 180.0)
_DWW = _pchip(_DWW_TAB) if isinstance(_DWW_TAB, (list, tuple)) else (lambda x, w=float(_DWW_TAB): w)


def _smin(a: float, b: float, p: float = 6.0) -> float:
    """Myk minimumsfunksjon for positive tall: ingen knekk langs skroget der
    grensen tar over."""
    if a <= 0.0 or b <= 0.0:
        return max(min(a, b), 0.0)
    return (a ** -p + b ** -p) ** (-1.0 / p)


def _nose(x: float) -> float:
    """Dekkslinjen rundes av helt forut (dekksplanen viser en rund nese, ikke
    en rett avkappet spiss): faktor 0 ved x = 0, 1 fra P.BOW_NOSE_L."""
    if x >= P.BOW_NOSE_L:
        return 1.0
    u = 1.0 - max(x, 0.0) / P.BOW_NOSE_L
    return math.sqrt(max(1.0 - u * u, 0.0))


def _sigma(m: int):
    """Andeler av buelengden for m punkter langs siden, litt tettere ved
    kjolen. Samme liste for alle spant, saa splinene i loften faar samme
    parametrisering (og knutevektor) fra baug til hekk."""
    u = np.linspace(0.0, 1.0, m)
    return 0.55 * u + 0.45 * u * u


_GEOM: dict = {}


def _section_geom(x: float) -> dict:
    """Spantets geometri ved x, regnet en gang og husket: tett polylinje fra
    kjolen til den virtuelle dekkskanten, avrundingen mot dekket og dekks-
    buen."""
    g = _GEOM.get(x)
    if g is not None:
        return g
    t = x / P.LOA
    k = _nose(x)
    # Senterlinjen (profilen) er zp. Akter bygges den konvekse kanobunnen paa
    # et kjolpunkt DEADWOOD_H hoeyere, og bunnen trekkes ned til senterlinjen
    # etterpaa (doedtre med hul overgang, se params.DEADWOOD_H).
    zp = bottom_z(x)
    dwh = max(_DEADWOOD(x), 0.0)
    zb = zp + dwh
    zs = sheer_z(x)
    hb = max(deck_half_breadth(x) * k, 1e-3)
    cam = deck_camber(x) * k
    hgt = max(zs - zb, 1e-3)
    # helt forut er spantet lite og flatt: bunnreisning og utfall holdes
    # innenfor kordens helning, ellers ville hjoernet falt utenfor
    chi = math.degrees(math.atan2(hgt, hb))
    beta = math.radians(_smin(_DEADRISE(t), 0.6 * chi))
    phi = math.radians(_smin(_FLARE(t), 0.6 * (90.0 - chi)))
    n = _NEXP(t)
    ub = np.array([math.cos(beta), math.sin(beta)])
    us = np.array([math.sin(phi), math.cos(phi)])
    det = math.cos(beta + phi)

    # avrundet dekkskant: radius DECK_EDGE_R mellom siden og dekksbuen
    sl = 2.0 * cam / hb                                # dekkets helning ved kanten
    td = np.array([-1.0, sl]) / math.hypot(1.0, sl)   # langs dekket, innover
    alpha = math.acos(min(1.0, max(-1.0, float(-us @ td))))
    tah = math.tan(0.5 * alpha)
    c0 = (hgt * math.cos(beta) - hb * math.sin(beta)) / det
    R = _smin(P.DECK_EDGE_R, min(0.3 * hgt, 0.3 * hb, 0.5 * max(c0, 1e-3) * tah))
    L = R / tah
    # Den virtuelle kanten (skjaeringen mellom side og dekk) skyves ut saa
    # avrundingens ytterste punkt ligger paa den maalte dekkslinjen: bredden
    # i plan er uendret.
    bd = hb + L * math.sin(phi) - R * (1.0 - math.cos(phi))
    D = np.array([bd, zs + cam * (1.0 - (bd / hb) ** 2)])

    # kjol og stevn: V-en faar en liten radius i bunnen (P.STEM_R i
    # vannlinjene), og spissen legges saa langt ned at den avrundede bunnen
    # gaar noyaktig gjennom kjolpunktet paa profilen
    rs = 0.0
    zk = zb
    if beta > 1e-3:
        x0, x1 = max(x - 5.0, 0.0), x + 5.0
        slope = abs(bottom_z(x1) - bottom_z(x0)) / (x1 - x0)
        a0 = (bd * math.cos(phi) - (D[1] - zb) * math.sin(phi)) / det
        rs = min(P.STEM_R / max(slope, 0.15), 0.3 * a0 / math.tan(beta))
        zk = zb - rs * (1.0 / math.cos(beta) - 1.0)
    K = np.array([0.0, zk])
    a, c = np.linalg.solve(np.array([ub, us]).T, D - K)
    H = K + a * ub

    # tett polylinje; th fordeles slik at punktene ligger omtrent jevnt
    u = np.linspace(0.0, 1.0, 2401)
    th = 0.5 * math.pi * u * u * (3.0 - 2.0 * u)
    f = np.sin(th) ** (2.0 / n)
    gg = np.cos(th) ** (2.0 / n)
    pts = H - (a * (1.0 - f))[:, None] * ub + (c * (1.0 - gg))[:, None] * us
    pts[0], pts[-1] = K, D
    if rs > 0.0:
        keep = (pts - K) @ ub > rs * math.tan(beta) + 1e-6
        F = np.array([0.0, zk + rs / math.cos(beta)])
        ang = np.linspace(-0.5 * math.pi, -0.5 * math.pi + beta, 25)
        foot = F + rs * np.c_[np.cos(ang), np.sin(ang)]
        foot[0] = (0.0, zb)
        pts = np.vstack([foot[:-1], pts[keep]])
    if dwh > 0.5:
        tt = np.clip(pts[:, 0] / _DWW(x), 0.0, 1.0)
        pts[:, 1] -= dwh * (1.0 - tt * tt) ** 2
        pts[0] = (0.0, zp)
    seg = np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))
    s = np.r_[0.0, np.cumsum(seg)]

    # avrundingen: fra punktet L foer kanten langs siden til punktet L
    # innenfor kanten langs dekket; en rasjonal kvadratisk Bezier (et
    # kjeglesnitt), som er en sirkelbue naar siden er rett der
    s1 = s[-1] - L
    T1 = np.array([np.interp(s1, s, pts[:, 0]), np.interp(s1, s, pts[:, 1])])
    j = int(np.searchsorted(s, s1))
    t1 = pts[min(j + 1, len(pts) - 1)] - pts[max(j - 1, 0)]
    t1 /= np.linalg.norm(t1)
    # kontrollpunktet: der tangenten i T1 krysser dekkets tangent i kanten
    M = np.array([t1, -td]).T
    lam = np.linalg.solve(M, D - T1)
    P1 = T1 + lam[0] * t1
    leg = lam[0]
    y2 = P1[0] + leg * td[0]
    T2 = np.array([y2, zs + cam * (1.0 - (y2 / hb) ** 2)])
    t2 = np.array([-1.0, 2.0 * cam * y2 / hb ** 2])
    t2 /= np.linalg.norm(t2)
    ca = float(np.clip((T1 - P1) @ (T2 - P1) / (np.linalg.norm(T1 - P1) * np.linalg.norm(T2 - P1)), -1, 1))
    w = math.sin(0.5 * math.acos(ca))
    g = dict(x=x, pts=pts, s=s, K=np.array([0.0, zp]), D=D, T1=T1, t1=t1, P1=P1,
             T2=T2, t2=t2, w=w, R=R, L=L, hb=hb, bd=bd, zs=zs, zb=zb, cam=cam,
             phi=phi, beta=beta, n=n, rs=rs, a=a, c=c)
    if len(_GEOM) > 50000:
        _GEOM.clear()
    _GEOM[x] = g
    return g


def _resample(g: dict, s_end: float, m: int):
    """m punkter langs sidekurven fra kjolen til buelengden s_end."""
    se = _sigma(m) * s_end
    return np.c_[np.interp(se, g["s"], g["pts"][:, 0]), np.interp(se, g["s"], g["pts"][:, 1])]


def section(x: float, n: int = 26):
    """Tverrsnitt ved stasjon x: liste med n punkter (y, z) fra kjolen eller
    stevnen til den virtuelle dekkskanten (skjaeringen mellom siden og
    dekksbuen, uten avrundingen). Punktene ligger jevnt langs kurven, litt
    tettere ved kjolen."""
    g = _section_geom(x)
    out = _resample(g, g["s"][-1], max(int(n), 4))
    out[0] = g["K"]
    out[-1] = g["D"]
    return [(float(y), float(z)) for y, z in out]


def section_parts(x: float, n_side: int = 28, n_corner: int = 9, n_deck: int = 15) -> dict:
    """Spantet slik loften bygges: siden fra kjolen til avrundingen, den
    avrundede dekkskanten og dekksbuen tvers over (styrbord til babord).
    Hver del samples med de samme parameterverdiene ved alle stasjoner.
    Tangentene (y, z) i skjoetene gjoer spantet glatt (G1) rundt hele."""
    g = _section_geom(x)
    side = _resample(g, g["s"][-1] - g["L"], n_side)
    side[0] = g["K"]
    side[-1] = g["T1"]
    tb = np.linspace(0.0, 1.0, n_corner)
    P0, P1, P2, w = g["T1"], g["P1"], g["T2"], g["w"]
    b0, b1, b2 = (1 - tb) ** 2, 2 * w * tb * (1 - tb), tb ** 2
    corner = (b0[:, None] * P0 + b1[:, None] * P1 + b2[:, None] * P2) / (b0 + b1 + b2)[:, None]
    corner[0], corner[-1] = P0, P2
    y2 = float(P2[0])
    yd = np.linspace(y2, -y2, n_deck)
    deck = np.c_[yd, g["zs"] + g["cam"] * (1.0 - (yd / g["hb"]) ** 2)]
    deck[0] = P2
    deck[-1] = (-P2[0], P2[1])
    return dict(side=side, corner=corner, deck=deck,
                side_par=_sigma(n_side), corner_par=tb, deck_par=np.linspace(0.0, 1.0, n_deck),
                t_keel=(1.0, 0.0), t_side=tuple(g["t1"]), t_deck=tuple(g["t2"]))


def wl_half_breadth(x: float) -> float:
    """Halvbredde i DWL, slik spantformen gir den (0 der kjolpunktet ligger
    over vannlinjen)."""
    g = _section_geom(x)
    p = g["pts"]
    if p[0, 1] >= 0.0:
        return 0.0
    return float(np.interp(0.0, p[:, 1], p[:, 0]))


def deck_camber(x: float) -> float:
    """Dekksbuens hoyde paa senterlinjen over dekkskanten."""
    return P.DECK_CAMBER * min(1.0, deck_half_breadth(x) / 900.0)


def deck_z(x: float, y: float = 0.0) -> float:
    """Dekkets hoyde over DWL ved (x, y)."""
    hb = max(deck_half_breadth(x), 1.0)
    t = min(abs(y) / hb, 1.0)
    return sheer_z(x) + deck_camber(x) * (1.0 - t * t)


def deck_arc(x: float, n: int = 13):
    """Punkter tvers over dekket fra styrbord til babord virtuelle dekkskant
    (der section() slutter)."""
    g = _section_geom(x)
    bd = g["bd"]
    return [
        (a * bd, g["zs"] + g["cam"] * (1.0 - (a * bd / g["hb"]) ** 2))
        for a in [(1.0 - 2.0 * i / n) for i in range(n + 1)]
    ]


def section_inner(x: float, wall: float, deck_t: float, n: int = 22):
    """Innsiden av skallet ved stasjon x: det ytre snittet flyttet `wall`
    innover langs normalen, kappet i senterlinjen og under dekket.

    En skalert kopi av snittet (slik det var foer) blir ikke en parallell
    kurve: i baugen, der snittet er en tynn kile, ble veggen bare 5-15 mm
    i stedet for 45, og hulrommet brot gjennom stevnen. Den ekte
    forskyvningen gir `wall` overalt, og hulrommet begynner foerst der
    skroget er bredt nok (over 2 x wall) - nedenfor er stevnen massiv.

    Returnerer None der det ikke blir plass til noe hulrom.
    """
    outer = np.asarray(section(x, n=max(4 * n, 80)), dtype=float)
    zs = sheer_z(x) - deck_t
    if len(outer) < 3 or zs - outer[0, 1] <= 12.0:
        return None
    # tangent (sentraldifferanse) dreid 90 grader = normal innover
    d = np.gradient(outer, axis=0)
    L = np.hypot(d[:, 0], d[:, 1])
    L[L < 1e-9] = 1.0
    t = d / L[:, None]
    inner = outer + wall * np.c_[-t[:, 1], t[:, 0]]

    # kapp i senterlinjen: punktet etter SISTE punkt med y <= 0, og
    # krysningen foer det. Rett over DWL i forfoten kan forskyvningen gaa i
    # loekke over senterlinjen; med foerste krysning fikk snittet da en
    # null-bred fold langs senterlinjen (tusenvis av degenererte trekanter).
    nonpos = np.where(inner[:, 0] <= 0.0)[0]
    k = int(nonpos[-1]) + 1 if len(nonpos) else 0
    if k >= len(inner):
        return None
    if k > 0:
        a, b = inner[k - 1], inner[k]
        f = -a[0] / (b[0] - a[0])
        start = np.array([0.0, a[1] + f * (b[1] - a[1])])
    else:
        start = np.array([0.0, inner[0, 1]])
    pts = np.vstack([start, inner[k:]])
    # doedtreet (DEADWOOD_H) er massivt: hulrommet faar et flatt gulv en vegg
    # over kjolpunktet til den konvekse kanobunnen. Ellers gaar den hule
    # overgangen inn i den smale finnen, og kordene (n punkter) kutter veggen.
    g = _section_geom(float(x))
    if g is not None and g.get("zb", g["K"][1]) - g["K"][1] > 0.5:
        zf = float(g["zb"]) + wall
        up = np.where(pts[:, 1] >= zf)[0]
        if len(up) == 0:
            return None
        j = int(up[0])
        if j > 0:
            a, b = pts[j - 1], pts[j]
            f = (zf - a[1]) / (b[1] - a[1])
            yc = a[0] + f * (b[0] - a[0])
            pts = np.vstack([[0.0, zf], [yc, zf], pts[j:]])
    # kapp under dekket: behold z < zs, legg til krysningen
    below = pts[:, 1] < zs
    if below.sum() < 2:
        return None
    m = np.where(~below)[0]
    if len(m):
        j = m[0]
        a, b = pts[j - 1], pts[j]
        f = (zs - a[1]) / (b[1] - a[1])
        pts = np.vstack([pts[:j], [a[0] + f * (b[0] - a[0]), zs]])
    pts[:, 0] = np.maximum(pts[:, 0], 0.0)
    if pts[:, 0].max() <= 12.0 or pts[-1, 1] - pts[0, 1] <= 12.0:
        return None

    # jevn fordeling langs kurven, n punkter
    seg = np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    if cum[-1] <= 1e-6:
        return None
    s = np.linspace(0.0, cum[-1], n)
    out = np.c_[np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])]
    out[0, 0] = 0.0
    return [(float(y), float(z)) for y, z in out]


def deck_arc_inner(x: float, wall: float, deck_t: float, n: int = 11):
    hb = deck_half_breadth(x) - wall
    return [
        (a * hb, deck_z(x, a * hb) - deck_t)
        for a in [(1.0 - 2.0 * i / n) for i in range(n + 1)]
    ]


def stations(count: int = 40):
    """Stasjoner med cosinusfordeling - tettest der formen endrer seg raskest."""
    t = np.linspace(0.0, 1.0, count)
    s = 0.5 * (1.0 - np.cos(np.pi * t))
    return [float(v) for v in s * P.LOA]


def displaced_volume_m3(n_stations: int = 200) -> float:
    """Kanobunnens volum under DWL (uten kjol og ror), ved integrasjon av
    spantarealene til spantformen i section()."""
    xs = np.linspace(P.LWL_FWD, max(P.LWL_AFT, P.TRANSOM_WL_X), n_stations)
    area = []
    for x in xs:
        p = _section_geom(float(x))["pts"]
        if p[0, 1] >= -1.0:
            area.append(0.0)
            continue
        zz = np.linspace(p[0, 1], 0.0, 80)
        yy = np.interp(zz, p[:, 1], p[:, 0])
        area.append(2.0 * float(np.trapezoid(yy, zz)))
    return float(np.trapezoid(area, xs)) / 1e9
