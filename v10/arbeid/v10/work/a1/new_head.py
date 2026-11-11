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
# Forstevnen over vann: z = stevnhodet * t^_STEM_EXP, t = 1 i baugen og 0 i
# vannlinjens forkant. Formelen flater kunstig ut (vannrett) rett over DWL,
# saa den brukes bare fram til _STEM_FIT_X1; derfra tar splinen den videre
# inn i den sporede forfoten uten knekk.
_STEM_EXP = 1.30
_STEM_FIT_X1 = 850.0
_TRACE_X1 = 2800.0      # sporet kanobunn hit; aktenfor begynner kjolens rotkurve
_BOTTOM_KNOTS = (300, 600, 900, 1250, 1700, 2200, 2800, 3500, 4200, 5000, 5800,
                 6500, 7100, 7500, 7800)


def _bottom_spline():
    top = _SHEER(0.0)
    sx = np.arange(0.0, _STEM_FIT_X1 + 1.0, 25.0)
    sz = top * ((P.LWL_FWD - sx) / P.LWL_FWD) ** _STEM_EXP
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
    """
    return _BOTTOM(x)


# --------------------------------------------------- tverrsnittets tabeller
_TABLES: dict = {}


def _natural_cubic(pairs):
    """Naturlig kubisk spline gjennom tabellpunktene: 2. derivert i hvert
    punkt (C2, ingen knekk der tabellen skifter helning)."""
    xs = [float(p[0]) for p in pairs]
    ys = [float(p[1]) for p in pairs]
    n = len(xs)
    A = np.zeros((n, n))
    r = np.zeros(n)
    A[0, 0] = A[-1, -1] = 1.0
    for i in range(1, n - 1):
        h0, h1 = xs[i] - xs[i - 1], xs[i + 1] - xs[i]
        A[i, i - 1], A[i, i], A[i, i + 1] = h0, 2.0 * (h0 + h1), h1
        r[i] = 6.0 * ((ys[i + 1] - ys[i]) / h1 - (ys[i] - ys[i - 1]) / h0)
    return xs, ys, [float(v) for v in np.linalg.solve(A, r)]


def _table(pairs, t: float) -> float:
    """Tabellverdi ved t: glatt (C2) mellom punktene, endeverdien utenfor."""
    key = tuple(tuple(p) for p in pairs)
    if key not in _TABLES:
        _TABLES[key] = _natural_cubic(pairs)
    xs, ys, M = _TABLES[key]
    if t <= xs[0]:
        return ys[0]
    if t >= xs[-1]:
        return ys[-1]
    i = min(bisect.bisect_right(xs, t) - 1, len(xs) - 2)
    h = xs[i + 1] - xs[i]
    a, b = (xs[i + 1] - t) / h, (t - xs[i]) / h
    return a * ys[i] + b * ys[i + 1] + ((a ** 3 - a) * M[i] + (b ** 3 - b) * M[i + 1]) * h * h / 6.0


def fullness(x: float) -> float:
    """Eksponent i superellipsen for tverrsnittet ved stasjon x."""
    return _table(P.SECTION_FULLNESS, x / P.LOA)


_BW_MAX = P.WL_BEAM_FRACTION * max(_DECK(v) for v in np.arange(0.0, _DECK_X1, 5.0))


def wl_half_breadth(x: float) -> float:
    """Halvbredde i DWL. Gaar mot null i vannlinjens forkant; akter smalner
    den inn mot akterspeilet (tabellen gaar forbi t = 1) og holdes saa."""
    t = (x - P.LWL_FWD) / P.LWL
    if t <= 0.0:
        return 0.0
    return _BW_MAX * _table(P.WATERPLANE, t)


