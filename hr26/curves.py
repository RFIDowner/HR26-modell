"""Fairede kurver for skroget, lest fra data/hull_stations.csv.

Tabellen er hentet ut av profil- og dekksplantegningen i 1:50 fra
HR 26-brosjyren og fairet. Alle verdier i fullskala mm: x maalt fra
baugen og akterover, z fra konstruksjonsvannlinjen (DWL), y halvbredde.
Fenderlistens senterlinje ligger i tabellen; dekkskanten (den tynne linjen
over listen i profilen) ligger i P.DECK_EDGE_Z.
"""
from __future__ import annotations

import csv
import os

import numpy as np

from . import params as P

_DATA = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data", "hull_stations.csv")
)


def _load():
    x, hb, zk, zb = [], [], [], []
    with open(_DATA, newline="") as fh:
        for row in csv.DictReader(fh):
            x.append(float(row["x_from_bow_mm"]))
            hb.append(float(row["deck_half_breadth_mm"]))
            zk.append(float(row["strake_z_mm"]))        # fenderlistens senterlinje
            zb.append(float(row["canoe_bottom_z_mm"]))
    x = np.array(x)
    # dekkskanten fra den maalte tabellen, resamplet paa stasjonene
    zs = np.interp(x, [p[0] for p in P.DECK_EDGE_Z], [p[1] for p in P.DECK_EDGE_Z])
    return x, np.array(hb), np.array(zk), zs, np.array(zb)


def _fair(y, passes=3, w=5):
    out = np.asarray(y, dtype=float).copy()
    k = np.ones(w) / w
    h = w // 2
    for _ in range(passes):
        out[h:-h] = np.convolve(out, k, "valid")
    return out


_X, _HB, _ZK, _ZS, _ZB = _load()
_HB = _fair(_HB, passes=2)
_ZK = _fair(_ZK, passes=2)
_ZS = _fair(_ZS, passes=2)
_ZB = _fair(_ZB, passes=8)


# Akterspeilet er en rett, tverrgaaende kant. I dekksplanen moetes derfor
# de to sidelinjene i hjornene, og sporingen tolker det som at skroget
# smalner av til en spiss. Halvbredden holdes derfor fast fra TRANSOM_X og
# akterover, med en svak innsmalning, slik at hekken faar den flate
# akterspeilflaten den skal ha.
TRANSOM_X = 7680.0
TRANSOM_TAPER = 0.95


def deck_half_breadth(x: float) -> float:
    """Halvbredde ved dekkskanten."""
    if x > TRANSOM_X:
        hb = float(np.interp(TRANSOM_X, _X, _HB))
        t = (x - TRANSOM_X) / (P.LOA - TRANSOM_X)
        return hb * (1.0 - (1.0 - TRANSOM_TAPER) * t)
    return float(np.interp(x, _X, _HB))


def sheer_z(x: float) -> float:
    """Dekkskantens hoyde over DWL (rekkas linje, over fenderlisten)."""
    return float(np.interp(x, _X, _ZS))


def strake_z(x: float) -> float:
    """Fenderlistens senterlinje over DWL."""
    return float(np.interp(x, _X, _ZK))


def bottom_z(x: float) -> float:
    """Kanobunnens hoyde over DWL (negativ under vann).

    Foran vannlinjens forkant foelger kurven forstevnen opp til stevnhodet.
    """
    if x < P.LWL_FWD:
        # forstevnen: fra stevnhodet i dekkshoyde ned til DWL
        t = (P.LWL_FWD - x) / P.LWL_FWD        # 1 ved baugen, 0 ved forkant DWL
        top = sheer_z(0.0)
        return float(top * (t ** 1.30))
    return float(np.interp(x, _X, _ZB))


def _table(pairs, t: float) -> float:
    return float(np.interp(t, [p[0] for p in pairs], [p[1] for p in pairs]))


def fullness(x: float) -> float:
    """Eksponent i superellipsen for tverrsnittet ved stasjon x."""
    return _table(P.SECTION_FULLNESS, x / P.LOA)


_BW_MAX = P.WL_BEAM_FRACTION * float(_HB.max())


def wl_half_breadth(x: float) -> float:
    """Halvbredde i DWL. Gaar mot null i vannlinjens forkant."""
    t = (x - P.LWL_FWD) / P.LWL
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        # akter for vannlinjen: hekkens bredde holdes
        return _BW_MAX * P.WATERPLANE[-1][1]
    return _BW_MAX * _table(P.WATERPLANE, t)


def section(x: float, n: int = 26):
    """Tverrsnitt ved stasjon x: liste med (y, z) fra kjoel/stevn til dekkskant.

    Under DWL beskrives formen av en superellipse mellom kjoelen og
    vannlinjebredden; over DWL gaar den jevnt ut til dekkskanten.
    """
    zb = bottom_z(x)
    zs = sheer_z(x)
    bd = max(deck_half_breadth(x), 1e-3)
    m = max(fullness(x), 1.02)

    pts = []
    if zb < -1.0:
        bw = min(wl_half_breadth(x), bd)
        k = max(8, int(n * 0.6))
        for i in range(k + 1):
            t = i / k
            z = zb * (1.0 - t)
            f = max(1.0 - (1.0 - t) ** m, 0.0)
            pts.append((bw * f ** (1.0 / m), z))
    else:
        # foran vannlinjen: snittet starter paa stevnen
        bw = min(wl_half_breadth(x) * 0.55, bd * 0.75)
        pts.append((0.0, zb))

    y0, z0 = pts[-1]
    k = max(6, n - len(pts))
    for i in range(1, k + 1):
        t = i / k
        z = z0 + (zs - z0) * t
        # eksponent > 1 gir loddrett topside ved vannlinjen, saa jevn
        # utfalling opp mot dekkskanten - ingen knekk i DWL
        y = y0 + (bd - y0) * (t ** 1.45)
        pts.append((y, z))

    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) > 1e-6 or abs(p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    return out


def deck_camber(x: float) -> float:
    """Dekksbuens hoyde paa senterlinjen over dekkskanten."""
    return P.DECK_CAMBER * min(1.0, deck_half_breadth(x) / 900.0)


def deck_z(x: float, y: float = 0.0) -> float:
    """Dekkets hoyde over DWL ved (x, y)."""
    hb = max(deck_half_breadth(x), 1.0)
    t = min(abs(y) / hb, 1.0)
    return sheer_z(x) + deck_camber(x) * (1.0 - t * t)


def deck_arc(x: float, n: int = 13):
    """Punkter tvers over dekket fra styrbord til babord dekkskant."""
    hb = deck_half_breadth(x)
    return [
        (a * hb, deck_z(x, a * hb))
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

    # kapp i senterlinjen: foerste punkt med y > 0, og krysningen foer det
    pos = np.where(inner[:, 0] > 0.0)[0]
    if len(pos) == 0:
        return None
    k = pos[0]
    if k > 0:
        a, b = inner[k - 1], inner[k]
        f = -a[0] / (b[0] - a[0])
        start = np.array([0.0, a[1] + f * (b[1] - a[1])])
    else:
        start = np.array([0.0, inner[0, 1]])
    pts = np.vstack([start, inner[k:]])
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
    """Deplasementsvolum under DWL ved Simpson-integrasjon av spantarealene."""
    xs = np.linspace(P.LWL_FWD, P.LWL_AFT, n_stations)
    area = []
    for x in xs:
        zb = bottom_z(x)
        if zb >= -1.0:
            area.append(0.0)
            continue
        bw = min(wl_half_breadth(x), deck_half_breadth(x))
        m = max(fullness(x), 1.02)
        zz = np.linspace(zb, 0.0, 60)
        t = 1.0 - zz / zb
        f = np.clip(1.0 - (1.0 - t) ** m, 0.0, None)
        yy = bw * f ** (1.0 / m)
        area.append(2.0 * float(np.trapezoid(yy, zz)))
    return float(np.trapezoid(area, xs)) / 1e9
