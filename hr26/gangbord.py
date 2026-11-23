"""Gangbordet og kanten opp til karmen (V11, 14.11.2026).

Brukeren (som kjenner baaten): «Rekka der du gaar, den er flat hele veien
rundt, og saa kommer det en kant, en forhoeyning opp» og «det finnes ingen 45
graders vinkel der». Ved trosse-snella akter gaar kanten «90 grader ned, altsaa
den er en buet kant, men den gaar ned til neste platå» (kant2.jpg).

V10 trinn 8 hadde en skraa skulder (40 grader) fra knekken opp til karmen og
akterdekket, og rekkepaalene aktenfor vinduet sto i skraaningen. Her er den
erstattet av:

* et flatt gangbord i knekkens hoeyde (C.knuckle_z, maalt i «nye (4)» og
  IMG_9374) fra skrogsiden og inn til en vegg. Gangbordet gaar rundt hjoernet
  og tvers over akterspeilet, der det ligger i dekkets hoeyde (knekken gaar
  over i dekkskanten ved 7 600-7 780, kant.jpeg);
* en nesten loddrett vegg (WALK_WALL_ANGLE) med rundet overkant (WALK_EDGE_R)
  opp til karmen og akterdekket. Veggen staar WALK_W_SIDE innenfor dekkskanten
  langs sidene, som ruffens side forut (SIDEDECK) og dekksplanens karm akter
  (dhb - 200), og WALK_W_AFT innenfor akterspeilets overkant;
* langs ruffen og sprayhoodens bein (forut for AFTDECK_X0) gaar veggen bare
  opp til dekket, WALK_CLEAR utenfor foten deres, saa lokket passer som foer.

Alt bygges som ett kutt (cutter): en rett (ruled) loft gjennom tverrsnitt
langs veggens fot i plan, fra styrbord rundt akterspeilet til babord. Hvert
tverrsnitt staar normalt paa veggen. Avrundingen er en del av tverrsnittet
og moeter toppflaten med en liten restvinkel (WALK_EXIT), saa kuttet aldri
tangerer en flate (OCC feiler paa tangerende kutt).
"""
from __future__ import annotations

import functools
import math

import cadquery as cq
import numpy as np

from . import cabin as CB
from . import curves as C
from . import deckhouse as D
from . import hull as H
from . import params as P

_TOP = 1500.0          # kuttets overkant over DWL
_OUT = 260.0           # kuttet gaar saa langt utenfor dekkskanten
_RISE = 20.0           # over toppflaten foer kuttet gaar loddrett opp
_N_BOT = 8             # punkter langs gangbordet i hvert tverrsnitt
_N_ARC = 6             # segmenter i avrundingen
_STEP = 40.0           # avstand mellom tverrsnittene langs veggen
_OBS_R = 8.0           # avrunding ved ruffens og sprayhoodens fot
_OBS_EXIT = 45.0       # ... og restvinkelen mot dekket der
_OBS_RISE = 4.0        # ... og hvor hoeyt over dekket foer kuttet gaar loddrett opp


def _smax(a: float, b: float, k: float) -> float:
    h = max(k - abs(a - b), 0.0) / k
    return max(a, b) + h * h * k / 4.0


# ------------------------------------------------------------ hindringer
@functools.lru_cache(maxsize=None)
def _cabin_xy():
    p = D._coach_planform().p
    return p[:, 0].copy(), p[:, 1].copy()


def _obstacle(x: float) -> float:
    """Halvbredden til det veggen maa gaa utenfor forut for akterdekket:
    ruffens fot (lokket) og sprayhoodens bein paa sidedekket. 0 der ingenting
    staar."""
    xs, ys = _cabin_xy()
    ob = 0.0
    if xs[0] <= x <= xs[-1]:
        ob = float(np.interp(x, xs, ys))
    xa, xb = P.COACH_X1 - 85.0, P.SPRAY_X1
    if xa <= x <= xb:
        ob = max(ob, CB._spray_deck_half_w(max(x, P.COACH_X1)))
    return ob


_TAPER = 260.0          # V11: bak sprayhoodens bein gaar veggen jevnt inn til dhb - WALK_W_SIDE


def _sstep(u: float) -> float:
    u = min(max(u, 0.0), 1.0)
    return u * u * (3.0 - 2.0 * u)


def walk_w(x: float) -> float:
    """Gangbordets bredde langs sidene, fra dekkskanten til veggens fot,
    aktenfor sprayhoodens bein. V11b: WALK_W_SIDE_TAB (glatt mellom
    punktene, konstant utenfor); V11: WALK_W_SIDE."""
    tab = getattr(P, "WALK_W_SIDE_TAB", None)
    if not tab:
        return P.WALK_W_SIDE
    if x <= tab[0][0]:
        return tab[0][1]
    for (x0, w0), (x1, w1) in zip(tab[:-1], tab[1:]):
        if x <= x1:
            return w0 + (w1 - w0) * _sstep((x - x0) / (x1 - x0))
    return tab[-1][1]


def _wall_fwd(x: float) -> float:
    y = C.deck_half_breadth(x) - P.WALK_W_SIDE
    ob = _obstacle(x)
    if ob > 0.0:
        y = _smax(y, ob + P.WALK_CLEAR, 40.0)
    return y


def side_wall_y(x: float) -> float:
    """Veggens fot i plan langs sidene (styrbord): utenfor ruffens og
    sprayhoodens fot forut, saa jevnt (smoothstep, uten knekk) ut til
    walk_w(x) innenfor dekkskanten (V11b: ferdig ved WALK_TAPER_X1, foer
    vinsjen)."""
    xb = P.SPRAY_X1
    if x <= xb:
        return _wall_fwd(x)
    base = C.deck_half_breadth(x) - walk_w(x)
    x1 = getattr(P, "WALK_TAPER_X1", xb + _TAPER)
    u = (x - xb) / (x1 - xb)
    if u >= 1.0:
        return base
    w = _sstep(u)
    return (1.0 - w) * _wall_fwd(xb) + w * base


def _transom_wall_x(y: float) -> float:
    return H._top_edge(abs(y))[0] - P.WALK_W_AFT


# ----------------------------------------------------------------- stien
@functools.lru_cache(maxsize=None)
def _path_stb():
    """Veggens fot i plan, styrbord halvdel, fra WALK_X0 til senterlinjen
    akter: tett polylinje (x, y)."""
    x1 = P.WALK_SIDE_END
    side = [(float(x), side_wall_y(float(x))) for x in np.arange(P.WALK_X0, x1 + 0.1, 5.0)]
    y2 = P.WALK_Y_AFT
    tr = [(_transom_wall_x(float(y)), float(y)) for y in np.arange(y2, -0.1, -5.0)]
    # hjoernet: Hermite-kurve med samme tangent som sidene og akterspeilet
    p0, p1 = np.array(side[-1]), np.array(tr[0])
    t0 = np.array(side[-1]) - np.array(side[-2])
    t1 = np.array(tr[1]) - np.array(tr[0])
    t0 /= np.linalg.norm(t0)
    t1 /= np.linalg.norm(t1)
    L = np.linalg.norm(p1 - p0)
    k = 1.09 * L      # Hermite-tangent ~ 3 x Bezier-haandtaket for en sirkelbue (ca. 67 graders sving)
    corner = []
    for u in np.linspace(0.0, 1.0, 120)[1:-1]:
        h00, h10 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u
        h01, h11 = -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
        q = h00 * p0 + h10 * k * t0 + h01 * p1 + h11 * k * t1
        corner.append((float(q[0]), float(q[1])))
    return np.array(side + corner + tr, dtype=float)


def _resample(pl: np.ndarray, step: float, keep_x=()):
    """Jevn avstand langs polylinjen; tverrsnitt ogsaa ved hver x i keep_x
    (paa sidene)."""
    d = np.r_[0.0, np.cumsum(np.hypot(*np.diff(pl, axis=0).T))]
    n = max(2, int(round(d[-1] / step)))
    ts = list(np.linspace(0.0, d[-1], n + 1))
    side = pl[:, 0] <= P.WALK_SIDE_END
    dks = [float(np.interp(xk, pl[side, 0], d[side])) for xk in keep_x]
    ts = [t for t in ts if all(abs(t - dk) > 0.6 * step for dk in dks)] + dks
    ts = np.array(sorted(ts))
    x = np.interp(ts, d, pl[:, 0])
    y = np.interp(ts, d, pl[:, 1])
    return np.c_[x, y]


def path(step_pair: bool = True):
    """Tverrsnittenes fotpunkter rundt hele hekken: styrbord forfra og
    akterover, tvers over akterspeilet og babord forover. Returnerer
    (punkter, utoverrettede normaler) i plan. Med step_pair et snittpar
    +-1 mm rundt trinnet ved AFTDECK_X0, der toppflaten skifter."""
    stb = _path_stb()
    xa = _x_switch()
    s = _resample(stb, _STEP, keep_x=(xa - 1.0, xa + 1.0) if step_pair else ())
    port = s[::-1].copy()
    port[:, 1] *= -1.0
    pts = np.vstack([s, port[1:]])
    t = np.gradient(pts, axis=0)
    t /= np.linalg.norm(t, axis=1)[:, None]
    # V11b: snittparet ved trinnet ligger 2 mm fra hverandre. Med litt ulik
    # normal krysset de to tverrsnittene hverandre (de er ca. 450 mm brede),
    # loften fikk negativt volum der, og hele kuttet tok ingenting. Tette par
    # faar derfor samme normal: parallelle plan.
    gap = np.hypot(*np.diff(pts, axis=0).T)
    for i in np.nonzero(gap < 0.5 * _STEP)[0]:
        m = t[i] + t[i + 1]
        t[i] = t[i + 1] = m / np.linalg.norm(m)
    n = np.c_[-t[:, 1], t[:, 0]]           # styrbord gaar akterover (+x): normal ut = +y
    # paa babord (motsatt vei) blir samme formel -y: utover der ogsaa
    return pts, n


# --------------------------------------------------------- hoeyder
def _drop(x: float) -> float:
    """Hvor langt gangbordet ligger under dekket. Ved skrogsiden er det
    knekkens hoeyde; innover foelger det dekkets bue (ca. 2 grader fall utover,
    som et sidedekk). Forut, der knekken naar dekkskanten, ligger flaten 3 mm
    over dekket (ikke noe kutt), og gangbordet vokser jevnt fram av dekket ved
    vinduets akterende. Akter (fra 6 500), der knekken gaar over i dekkskanten
    og gangbordet gaar tvers over akterspeilet, ligger det minst 2 mm under
    dekket, saa akterdekkets plate skjaeres helt bort og kuttet aldri tangerer
    dekket."""
    d = C.knuckle_drop(min(x, P.LOA))
    if x >= 6500.0:
        return _smax(d, 2.0, 4.0)
    if d >= 6.0:
        return d
    return d - 3.0 * (1.0 - d / 6.0) ** 2


def ledge_z(x: float, y: float) -> float:
    """Gangbordets hoeyde ved (x, y)."""
    xc = min(max(x, 0.0), P.LOA - 1.0)
    return C.deck_z(xc, y) - _drop(x)


def _x_switch() -> float:
    """Der tverrsnittet skifter fra veggen langs sprayhoodens bein til veggen
    med avrunding opp til akterdekket: 5 mm foran akterdekkets forkant
    (AFTDECK_X0) og bak sprayhoodens bein (SPRAY_X1). Laa overgangen (+-1 mm)
    over platens forkant, ble det smaa flater og ikke-manifolde kanter i STL-en
    (V11, foerste bygg)."""
    return P.AFTDECK_X0 - 5.0


def _top_z(x: float, y: float) -> tuple[float, bool]:
    """Toppflaten veggen gaar opp til, og om det er akterdekket/karmen
    (ellers dekket ved ruffens og sprayhoodens fot)."""
    if x >= _x_switch():
        return D.coaming_top_z(min(x, P.LOA)), True
    # 3 mm over dekket: da krysser dekket den lille buen midt paa, ikke i
    # endepunktet (med buens ende 0,2 mm fra dekket ble det kanter paa
    # 0,03-0,08 mm og ikke-manifolde kanter i STL-en ved 5 994)
    return C.deck_z(x, y) + 3.0, False


def on_ledge(x: float, y: float) -> bool:
    """Ligger punktet paa gangbordet (utenfor veggen)?"""
    if x < P.WALK_X0:
        return False
    if x <= P.WALK_SIDE_END - 50.0:
        return abs(y) > side_wall_y(x)
    pl = _path_stb()
    q = np.array([x, abs(y)])
    i = int(np.argmin(np.hypot(*(pl - q).T)))
    j = min(i + 1, len(pl) - 1)
    t = pl[j] - pl[max(i - 1, 0)]
    nrm = np.array([-t[1], t[0]])
    return float(np.dot(q - pl[i], nrm)) > 0.0


def surface_z(x: float, y: float) -> float:
    """Overflaten et beslag eller et hull staar paa: gangbordet der det er,
    ellers akterdekket/karmtoppen (fra AFTDECK_X0) eller dekket."""
    if on_ledge(x, y):
        return min(C.deck_z(x, y), ledge_z(x, y))
    return D.top_z(x, y)


def wall_y_at(x: float) -> float:
    """Veggens fot i plan (styrbord) ved x, langs sidene og rundt hjoernet
    (der stien fortsatt gaar akterover)."""
    if x <= P.WALK_SIDE_END:
        return side_wall_y(x)
    pl = _path_stb()
    m = pl[:, 1] >= P.WALK_Y_AFT
    xs, ys = pl[m, 0], pl[m, 1]
    k = int(np.argmax(xs))
    return float(np.interp(x, xs[:k + 1], ys[:k + 1]))


def hole_y(x: float, inset: float, r: float) -> float:
    """Halvbredden til et dekkshull (radius r) som skulle staa `inset` fra
    dekkskanten. Ligger det ikke helt ute paa gangbordet (minst 10 mm utenfor
    veggens fot), flyttes det inn paa den flate toppen, HOLE_TOP_CLEAR
    innenfor veggens fot, saa det aldri skjaerer veggen eller avrundingen
    (V11b: gangbordet er bare 45-55 mm bredt aktenfor vinsjen)."""
    y = C.deck_half_breadth(x) - inset
    if x < P.WALK_X0 or x > P.LOA:
        return y
    yw = wall_y_at(x)
    if y - r >= yw + 10.0:
        return y
    # inn paa toppen; i hjoernet staar veggen skraatt, saa avstanden maales
    # vinkelrett paa veggens fot (stien), ikke bare i y
    pl = _path_stb()
    clear = getattr(P, "HOLE_TOP_CLEAR", 85.0)
    y = min(y, yw - clear)
    while float(np.min(np.hypot(pl[:, 0] - x, pl[:, 1] - y))) < clear:
        y -= 2.0
    return y


def wall_frame(x: float):
    """Veggen ved x (styrbord side): fotpunktets y, retning langs veggen i
    plan (tx, ty, akterover), normal utover (nx, ny), gangbordets og
    toppflatens hoeyde."""
    yf = side_wall_y(x)
    d = 5.0
    t = np.array([2.0 * d, side_wall_y(x + d) - side_wall_y(x - d)])
    t /= np.linalg.norm(t)
    n = np.array([-t[1], t[0]])
    return yf, (float(t[0]), float(t[1])), (float(n[0]), float(n[1])), ledge_z(x, yf + 5.0), D.coaming_top_z(x)


# ------------------------------------------------------- tverrsnittet
def _section(p, n, shift: float):
    """Kuttets tverrsnitt i planet gjennom p langs n (utover), som liste av
    (s, z): s utover fra veggens fot. `shift` vokser kuttet saa mange mm inn i
    godset (behold-volumet for uthulingen)."""
    x, y = float(p[0]), float(p[1])
    z0 = ledge_z(x, y) - shift
    zt, aft = _top_z(x, y)
    zt = max(zt - shift, z0 + 12.0)
    if aft:
        a = math.radians(P.WALK_WALL_ANGLE)
        R, eps, rise_h = P.WALK_EDGE_R, math.radians(P.WALK_EXIT), _RISE
    else:
        # langs ruffen og sprayhoodens bein: loddrett vegg opp til dekket og
        # bare en liten avrunding, saa kuttet holder seg utenfor foten deres.
        # Buen maa likevel spenne 45 grader: med 5 grader ble kantene 0,07 mm,
        # og de boolske operasjonene feilet stille (kuttet tok ingenting).
        a = math.radians(90.0)
        R, eps, rise_h = _OBS_R, math.radians(_OBS_EXIT), _OBS_RISE
    R = max(min(R - shift, 0.4 * (zt - z0)), 2.0)
    sf = -shift / math.sin(a)                      # veggens fot
    # sirkelens sentrum: R fra veggen (inn i godset) og R*cos(eps) under toppen
    zc = zt - R * math.cos(eps)
    sc = sf - (R + (zc - z0) * math.cos(a)) / math.sin(a)
    phi1 = math.pi / 2.0 - a                       # tangent mot veggen
    phi2 = math.pi / 2.0 - eps                     # moeter toppen med restvinkel eps
    arc = [(sc + R * math.cos(f), zc + R * math.sin(f))
           for f in np.linspace(phi2, phi1, _N_ARC + 1)]
    t2 = arc[0]
    L = rise_h / math.sin(eps)
    rise = (t2[0] - L * math.cos(eps), t2[1] + rise_h)
    # gangbordet utover, fulgt i hoeyde punkt for punkt
    s_out = _out_extent(p, n)
    bot = []
    for s in np.linspace(sf, s_out, _N_BOT + 1)[1:]:
        q = p + s * n
        bot.append((float(s), ledge_z(float(q[0]), float(q[1])) - shift))
    poly = [(sf, z0)] + bot + [(s_out, _TOP), (rise[0], _TOP), rise] + arc
    return poly


def _out_extent(p, n) -> float:
    """Hvor langt utover tverrsnittet gaar: forbi dekkskanten med _OUT."""
    x, y = float(p[0]), abs(float(p[1]))
    if x <= P.WALK_SIDE_END - 50.0 and abs(n[0]) < 0.6:
        return C.deck_half_breadth(x) - y + _OUT
    return P.WALK_W_SIDE + _OUT


def _keep_section(p, n, shift: float):
    """Behold-volumets tverrsnitt: gangbordet og veggen forskjoevet `shift`
    inn i godset, uten avrunding og toppflate (de ligger over dekket, der
    det ikke er hulrom). Faa flater, saa uthulingen ikke faar smaa biter i
    overgangen ved AFTDECK_X0."""
    x, y = float(p[0]), float(p[1])
    a = math.radians(P.WALK_WALL_ANGLE)
    z0 = ledge_z(x, y) - shift
    sf = -shift / math.sin(a)
    s_out = _out_extent(p, n)
    bot = []
    for s in np.linspace(sf, s_out, _N_BOT + 1)[1:]:
        q = p + s * n
        bot.append((float(s), ledge_z(float(q[0]), float(q[1])) - shift))
    return [(sf, z0)] + bot + [(s_out, _TOP), (sf - (_TOP - z0) / math.tan(a), _TOP)]


def cutter(shift: float = 0.0) -> cq.Workplane:
    """Alt som skjaeres bort over gangbordet og utenfor veggen, begge sider
    og tvers over akterspeilet, i ett stykke. Med shift > 0: behold-volumet
    for uthulingen (veggen under gangbordet og bak kanten like tykk som
    skallet ellers)."""
    pts, nrm = path(step_pair=shift <= 0.0)
    wires = []
    for p, n in zip(pts, nrm):
        sec = _section(p, n, shift) if shift <= 0.0 else _keep_section(p, n, shift)
        vs = [cq.Vector(float(p[0] + s * n[0]), float(p[1] + s * n[1]), float(z)) for s, z in sec]
        wires.append(cq.Wire.makePolygon(vs, close=True))
    solid = cq.Solid.makeLoft(wires, ruled=True)
    if not solid.isValid():
        raise RuntimeError("ugyldig kutt for gangbordet")
    return cq.Workplane("XY").newObject([solid])
