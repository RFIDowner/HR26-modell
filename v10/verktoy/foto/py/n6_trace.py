"""Sporing i «nye (6).jpeg» (13.11.2026): baaten henger i stroppene paa
gaffeltrucken, sett skraatt akterfra paa styrbord laaring (akter til venstre,
baugen mot hoeyre kant), kameraet lavt (ca. vannlinjestripens hoeyde).
1170 x 1588, skjermklipp fra iPhone uten EXIF (ukjent brennvidde og
hovedpunkt), ikon nede til hoeyre.

Alle punkter er (u, v) i bildets piksler, u mot hoeyre, v nedover, origo oppe
til venstre, pikselsenter som i PIL. Lager ../out/n6_trace.json:

  strake     fenderlistens moerke baand paa styrbord side per kolonne
             [u, v_top, v_bot, v_mid] (u 252-1100; stropper og leideren ute)
  strake_tr  listen paa akterspeilet, babord del (venstre for rorhodet)
             [u, v_top, v_bot, v_mid] (u 100-141)
  boottop    [u, v_blaa_overkant, v_roedt_start] per kolonne (NaN der ikke funnet)
  keel_le    kjolens forkant per rad [v, u] (roedt mot bakgrunn, hoeyre kant)
  keel_te    kjolens bakkant per rad [v, u] (venstre kant; kjettingen ute)
  keel_bot   kjolens bunn per kolonne [u, v]
  aft_bot    skrogets nedre omriss mellom roret og kjolen per kolonne [u, v]
  rud_te     rorets bakkant per rad [v, u] (venstre kant)
  rud_le     rorets forkant under trinnet per rad [v, u] (hoeyre kant)
  rud_bot    rorets bunn per kolonne [u, v]
  rud_step   trinnets overkant (rorets fremre nedre del) per kolonne [u, v]
  rud_gap    den moerke linja (rorets forkant / akterspeilet) per rad [v, u]
  tr_corner  det naere akterspeilhjoernet over stripen [u, v, kontrast]
             (kanten lyst akterspeil -> moerkere skrogside, langs en haandlest guide)
  window     vinduets ytre ramme: bakerste og forreste punkt (haandlest paa
             5x, +-1,5 px)
  corner     listens ende ved det naere akterspeilhjoernet og ved det fjerne
             (haandlest, +-2 px)

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 --lock -- python n6_trace.py
"""
import numpy as np
from PIL import Image

import common as c

IMG = r"C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/nye (6).jpeg"
A = np.asarray(Image.open(IMG).convert("RGB")).astype(float)
H_, W_ = A.shape[:2]
R, G, B = A[..., 0], A[..., 1], A[..., 2]
Y = A.mean(axis=2)
CR = (R - np.maximum(G, B)) / (R + 10.0)       # roedhet: bunnstoff 0,5-1,0, bakgrunn < 0,1
BLU = B - R


def cross(prof, out_val, in_val, start, step):
    """Foerste subpiksel-indeks fra start (paa inn-siden) i retning step der
    prof krysser midt mellom in_val og out_val."""
    thr = 0.5 * (out_val + in_val)
    s = np.sign(in_val - out_val)
    i = start
    n = len(prof)
    while 0 <= i and i + step < n and i + step >= 0:
        a, b = prof[i], prof[i + step]
        if (a - thr) * s >= 0 > (b - thr) * s:
            t = (a - thr) / (a - b)
            return i + step * t
        i += step
    return np.nan


def guide(pts, u):
    p = np.asarray(pts, float)
    return np.interp(u, p[:, 0], p[:, 1])


def robust_keep(x, y, deg=4, k=3.0, floor=0.8, it=4):
    keep = np.ones(len(x), bool)
    for _ in range(it):
        cf = np.polyfit(x[keep], y[keep], deg)
        r = y - np.polyval(cf, x)
        s = 1.4826 * np.median(np.abs(r[keep]))
        keep = np.abs(r) < max(k * s, floor)
    return keep


# ------------------------------------------------------------ fenderlisten
STRAKE_G = [(250, 697), (300, 697), (400, 705), (500, 721), (600, 735), (700, 750), (800, 764), (880, 776),
            (950, 784), (1000, 791), (1050, 798), (1100, 806)]
STRAKE_MASK = [(418.0, 448.0), (890.0, 935.0)]     # leiderens rekke ender paa listen; bakre stropp


def band(u, g, half=15):
    r0 = int(round(g)) - half
    prof = Y[r0:r0 + 2 * half + 1, u]
    i = int(np.argmin(prof[half - 8:half + 9])) + half - 8
    top_bg = np.median(prof[:4])
    bot_bg = np.median(prof[-4:])
    mn = prof[i]
    if min(top_bg, bot_bg) - mn < 40:
        return None
    t = cross(prof, top_bg, mn, i, -1)
    b = cross(prof, bot_bg, mn, i, +1)
    if not (np.isfinite(t) and np.isfinite(b)):
        return None
    return r0 + t, r0 + b


def trace_strake():
    out = []
    for u in range(252, 1101):
        if any(a <= u <= b for a, b in STRAKE_MASK):
            continue
        r = band(u, guide(STRAKE_G, u), 15)
        if r is None:
            continue
        t, b = r
        w = b - t
        if not 6.0 < w < 20.0:
            continue
        out.append((u, t, b, 0.5 * (t + b), w))
    out = np.array(out)
    keep = robust_keep(out[:, 0], out[:, 3], deg=5)
    wmed = np.median(out[keep, 4])
    keep &= np.abs(out[:, 4] - wmed) < 4.0
    return out[keep]


def trace_strake_tr():
    out = []
    for u in range(100, 142):
        g = 733.0 + (u - 100.0) * (713.0 - 733.0) / 41.0
        r = band(u, g, 13)
        if r is None:
            continue
        t, b = r
        if not 5.0 < b - t < 16.0:
            continue
        out.append((u, t, b, 0.5 * (t + b)))
    return np.array(out)


# ------------------------------------------------------------ vannlinjestripen
def trace_boottop():
    out = []
    for u in range(135, 1076):
        g = 928.0 + (u - 135.0) * (945.0 - 928.0) / 940.0
        r0 = int(g) - 22
        cy = Y[r0:r0 + 50, u]
        cb = BLU[r0:r0 + 50, u]
        cr = CR[r0:r0 + 50, u]
        isb = (cb > 8) & (cy < 90)
        if isb.sum() < 4:
            continue
        idx = np.where(isb)[0]
        runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
        run = max(runs, key=len)
        if len(run) < 4 or run[0] < 4:
            continue
        b0, b1 = run[0], run[-1]
        white = np.median(cy[max(b0 - 7, 0):b0 - 2])
        blue = np.median(cy[b0 + 1:b1])
        top = cross(cy, white, blue, b0 + 1, -1)
        # roedt: foerste rad under det blaa med roedhet > 0,35 i 3 rader
        red_c = np.nan
        for j in range(b1 + 1, len(cr) - 4):
            if (cr[j:j + 3] > 0.35).all():
                inside = np.median(cr[j + 1:j + 4])
                outside = np.median(cr[max(j - 4, b1):j - 1]) if j - 1 > b1 else cr[j - 1]
                red_c = cross(cr, outside, inside, j + 1, -1)
                break
        out.append((u, r0 + top, r0 + red_c if np.isfinite(red_c) else np.nan))
    out = np.array(out, float)
    keep = robust_keep(out[:, 0], out[:, 1], deg=4, floor=1.0)
    out[~keep, 1] = np.nan
    ok = np.isfinite(out[:, 2])
    k2 = np.zeros(len(out), bool)
    k2[ok] = robust_keep(out[ok, 0], out[ok, 2], deg=4, floor=1.0)
    out[~k2, 2] = np.nan
    return out


# ------------------------------------------------------------ roedt omriss
THR = 0.30


def red_edge_col(u, v_lo, v_hi, down=True, run=4):
    """Nedre (down) eller oevre kant av det roede i kolonne u, mellom v_lo og
    v_hi. Leter fra bakgrunnssiden mot et loep paa run roede piksler."""
    prof = CR[:, u]
    vs = np.arange(v_lo, v_hi)
    red = prof[vs] > THR
    if down:
        k = len(vs) - 1
        while k >= run:
            if red[k - run + 1:k + 1].all():
                last = vs[k]
                inside = np.median(prof[last - 6:last - 1])
                outside = np.median(prof[last + 3:last + 8])
                return cross(prof, outside, inside, last - 2, +1)
            k -= 1
    else:
        k = 0
        while k < len(vs) - run:
            if red[k:k + run].all():
                first = vs[k]
                inside = np.median(prof[first + 1:first + 6])
                outside = np.median(prof[first - 7:first - 2])
                return cross(prof, outside, inside, first + 2, -1)
            k += 1
    return np.nan


def red_edge_row(v, u_lo, u_hi, side, run=4):
    """Roedt omriss i rad v: side -1 = venstre kant, +1 = hoeyre kant."""
    prof = CR[v, :]
    us = np.arange(u_lo, u_hi)
    red = prof[us] > THR
    if side < 0:
        k = 0
        while k < len(us) - run:
            if red[k:k + run].all():
                first = us[k]
                inside = np.median(prof[first + 1:first + 6])
                outside = np.median(prof[first - 7:first - 2])
                return cross(prof, outside, inside, first + 2, -1)
            k += 1
        return np.nan
    k = len(us) - 1
    while k >= run:
        if red[k - run + 1:k + 1].all():
            last = us[k]
            inside = np.median(prof[last - 6:last - 1])
            outside = np.median(prof[last + 3:last + 8])
            return cross(prof, outside, inside, last - 2, +1)
        k -= 1
    return np.nan


def rows(fn, vs):
    out = []
    for v in vs:
        x = fn(v)
        if np.isfinite(x):
            out.append((v, x))
    return np.array(out)


def cols(fn, us):
    out = []
    for u in us:
        y = fn(u)
        if np.isfinite(y):
            out.append((u, y))
    return np.array(out)


def trace_keel():
    le = rows(lambda v: red_edge_row(v, 700, 960, +1), range(1050, 1262))
    # bakkanten: kjettingen henger rett til venstre (u 605-630, v 1095-1245);
    # let fra u 622 og hoeyreover, bakkanten er hvit bakgrunn -> roedt
    te = rows(lambda v: red_edge_row(v, 612 if v > 1150 else 624, 720, -1), range(1100, 1278))
    bot = cols(lambda u: red_edge_col(u, 1200, 1310, True), range(626, 790))
    return le, te, bot


def trace_aft_bottom():
    # nedre kant av skroget mellom roret (trinnets ende u ~ 330) og kjolen
    return cols(lambda u: red_edge_col(u, 1040, 1088 if u < 335 else 1110, True), range(255, 612))


def trace_rudder():
    te = rows(lambda v: red_edge_row(v, 60, 200, -1), range(952, 1266))
    le = rows(lambda v: red_edge_row(v, 236, 380, +1), range(1097, 1262))
    bot = cols(lambda u: red_edge_col(u, 1220, 1310, True), range(100, 252))
    # trinnet: en tynn moerk linje (spalte) mellom skrogets bunn og rorets
    # fremre nedre del, v ~ 1088-1095: minimum av Y per kolonne
    step = []
    for u in range(256, 324):
        seg = Y[1082:1100, u]
        i = int(np.argmin(seg))
        if 1 <= i < len(seg) - 1:
            a, b_, cc = seg[i - 1], seg[i], seg[i + 1]
            d = 0.5 * (a - cc) / (a - 2 * b_ + cc + 1e-9)
            step.append((u, 1082 + i + d))
    step = np.array(step)
    # moerk linje (rorets forkant mot akterspeilet/skroget) i det roede: minimum av Y
    gap = []
    for v in range(952, 1082):
        seg = Y[v, 225:275]
        i = int(np.argmin(seg))
        if 1 <= i < len(seg) - 1:
            a, b_, cc = seg[i - 1], seg[i], seg[i + 1]
            d = 0.5 * (a - cc) / (a - 2 * b_ + cc + 1e-9)
            gap.append((v, 225 + i + d, float(np.median(seg) - b_)))
    return te, le, bot, step, np.array(gap)


# ------------------------------------------------------------ akterspeilets hjoerne
# Det naere (styrbord) hjoernet mellom akterspeilet (lyst, flatt) og
# skrogsiden (moerkere): fra listen ved u ~ 477 buer det ned og innover til
# vannlinjestripen ved u ~ 345. Per rad (der kanten er bratt) og per kolonne
# (der den flater ut mot stripen). Leiderplattformen (v 816-860) og rekka er ute.
CORNER_G = [(478.0, 735.0), (469.0, 770.0), (465.0, 800.0), (461.0, 811.0), (446.0, 845.0), (440.0, 850.0),
            (430.0, 862.0), (420.0, 870.0), (410.0, 877.0), (400.0, 884.0), (390.0, 891.0), (380.0, 897.0),
            (370.0, 903.0), (360.0, 909.0), (350.0, 914.0), (344.0, 916.5)]   # (u, v), haandlest paa 5x


def trace_tr_corner(step=1.5, half=8):
    """Langs den haandleste guiden: stoerste retningsderiverte (lyst -> moerkt
    utover mot skrogsiden) paa normalen, glattet bilde (sigma 1,5 px)."""
    from scipy import ndimage as ndi
    Ys = ndi.gaussian_filter(Y, 1.5)
    g = np.asarray(CORNER_G, float)
    seg = np.diff(g, axis=0)
    L = np.r_[0.0, np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))]
    out = []
    for s_ in np.arange(0.0, L[-1], step):
        p = np.array([np.interp(s_, L, g[:, 0]), np.interp(s_, L, g[:, 1])])
        if 812.0 <= p[1] <= 848.0 or (p[0] > 395.0 and p[1] > 846.0 and p[1] < 858.0):
            continue                                    # leiderplattformen og knotten
        j = min(int(np.searchsorted(L, s_, side="right")) - 1, len(seg) - 1)
        t = seg[j] / np.hypot(*seg[j])
        n = np.array([-t[1], t[0]])                     # normal; pek mot skrogsiden (hoeyre/ned)
        if n[0] + n[1] < 0:
            n = -n
        ks = np.arange(-half, half + 0.01, 0.5)
        uu, vv = p[0] + ks * n[0], p[1] + ks * n[1]
        prof = ndi.map_coordinates(Ys, [vv, uu], order=1)
        d = np.gradient(prof, 0.5)
        i = int(np.argmin(d))
        if d[i] > -1.5 or not 1 <= i <= len(d) - 2:
            continue
        y0, y1, y2 = d[i - 1], d[i], d[i + 1]
        off = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-9)
        k = ks[i] + 0.5 * off
        q = (p[0] + k * n[0], p[1] + k * n[1], -float(d[i]))
        if q[1] < 914.5:                                # ikke stripens overkant
            out.append(q)
    return np.array(out)


# vinduets ytre ramme (haandlest paa 5x): bakre ende (rund, oeverst) og
# forreste punkt (nederst i den skraa forenden)
WINDOW = dict(aft_end=[992.5, 748.0], fwd_end=[1096.5, 800.5],
              aft_top=[995.0, 736.0], aft_bot=[1013.0, 786.0], fwd_top=[1084.0, 767.0])
# listens ender ved akterspeilet (haandlest): naer side (der gummilista slutter
# og stalbeslaget begynner) og fjern side (mot himmelen/trucken)
CORNER = dict(near_rubber_end=[248.0, 697.5], far_end=[98.5, 735.0])


if __name__ == "__main__":
    st = trace_strake()
    stt = trace_strake_tr()
    bt = trace_boottop()
    kle, kte, kbo = trace_keel()
    ab = trace_aft_bottom()
    rte, rle, rbo, rst, rgap = trace_rudder()
    tc = trace_tr_corner()
    print("tr_corner %d" % len(tc), np.round(tc[::12], 1).tolist())
    print("strake %d (u %.0f-%.0f, bredde %.1f), strake_tr %d, boottop %d (roedt %d)" % (
        len(st), st[0, 0], st[-1, 0], np.median(st[:, 4]), len(stt), np.isfinite(bt[:, 1]).sum(),
        np.isfinite(bt[:, 2]).sum()))
    print("keel le %d te %d bot %d, aft_bot %d, rudder te %d le %d bot %d step %d gap %d" % (
        len(kle), len(kte), len(kbo), len(ab), len(rte), len(rle), len(rbo), len(rst), len(rgap)))
    for nm, a in (("keel_le", kle), ("keel_te", kte), ("keel_bot", kbo), ("aft_bot", ab), ("rud_te", rte),
                  ("rud_le", rle), ("rud_bot", rbo), ("rud_step", rst)):
        print(nm, np.round(a[::max(len(a) // 8, 1)], 1).tolist())
    out = dict(image="nye (6).jpeg (1170 x 1588)", W=W_, H=H_, strake=st[:, :4], strake_tr=stt, boottop=bt,
               keel_le=kle, keel_te=kte, keel_bot=kbo, aft_bot=ab, rud_te=rte, rud_le=rle, rud_bot=rbo,
               rud_step=rst, rud_gap=rgap, tr_corner=tc, window=WINDOW, corner=CORNER, strake_mask=STRAKE_MASK,
               desc=__doc__)
    c.save_json(out, c.W + "/out/n6_trace.json")
