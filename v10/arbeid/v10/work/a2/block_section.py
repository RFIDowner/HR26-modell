# ------------------------------------------------------- tverrsnittets form
# Hvert spant er EN glatt, konveks kurve fra kjolen (eller stevnen) til
# dekkskanten. Hjoernet mellom en bunnlinje gjennom kjolpunktet (helning
# P.SECTION_DEADRISE) og en sidelinje gjennom dekkskanten (utfall
# P.SECTION_FLARE) rundes av med en superellipse med eksponent P.SECTION_N:
#
#   P(th) = H - a (1 - sin(th)^(2/n)) ub + c (1 - cos(th)^(2/n)) us
#
# der H er hjoernet, ub og us bunn- og siderretningen og th fra 0 (kjolen)
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


_FLARE = _pchip(P.SECTION_FLARE)
_NEXP = _pchip(P.SECTION_N)
_DEADRISE = _pchip(P.SECTION_DEADRISE)


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
    zb = bottom_z(x)
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
        ang = np.linspace(-0.5 * math.pi, -0.5 * math.pi + beta, 10)
        foot = F + rs * np.c_[np.cos(ang), np.sin(ang)]
        foot[0] = (0.0, zb)
        pts = np.vstack([foot[:-1], pts[keep]])
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
    g = dict(x=x, pts=pts, s=s, K=np.array([0.0, zb]), D=D, T1=T1, t1=t1, P1=P1,
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
