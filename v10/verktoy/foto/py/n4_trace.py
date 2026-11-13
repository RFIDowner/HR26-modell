"""Sporing i «nye (4).jpeg» (13.11.2026): babord side, baaten paa land paa
stoetter, litt forfra, kameraet lavt (omtrent i hoeyde med stripen). 1170 x 831,
iPhone-skjermklipp uten EXIF.

Alle punkter er (u, v) i bildets piksler, u mot hoeyre, v nedover, origo oppe
til venstre, pikselsenter som i PIL (u = kolonneindeks).

Lager ../out/n4_trace.json:
  strake    fenderlistens morke band per kolonne [u, v_top, v_bot, v_mid]
  stem      stevnens ytterste kant per rad (lyst skrog mot bakgrunn) [v, u],
            rad 380-468 (over det henger en fender/slange foran stevnen)
  crease    den tynne morke linja 18-24 px innenfor [v, u] = VAAR stevn. Det
            lyse baandet utenfor er en annen baat (samme fargeskjema) som
            staar lenger unna bak vaar stevn: stripen dens ligger 12 px hoeyere
            og er 40 % tynnere, baandet begynner der dens dekk er (rad ~378),
            og over det er vaar stevn ytterst (stem_hi, paa linje med crease)
  stem_hi   ytterste lyse kant rad 338-376 (= fortsettelsen av crease) [v, u]
  stem_wl   vaar stevn ved stripen [v, u]: rad 472-476 (vaart krem mot den
            andre baatens blaa) og 484-497 (vaart blaa mot dens hvite/roede)
  sheer     skrogets overkant mot himmelen ved baugen [u, v] (u 60-400)
  stern     skrogets akterste kant per rad [v, u] (akterspeilets hjoerne mot
            den blaa presenningen), rad 396-496
  strake_end listens akterende [u, v] (haandlest, 6x)
  boottop   per kolonne [u, v_blaa_overkant, v_blaa_underkant, v_roedt_start]
  bottom    skrogets nedre omriss per kolonne [u, v] (moerkt roedt mot bakgrunn)
  front     forfotens forkant per rad [v, u] (stripen og det roede mot bakgrunn)
  keel_le   kjolens forkant per rad [v, u], keel_te bakkant [v, u],
  keel_bot  kjolens bunn per kolonne [u, v]
  rudder    roret per rad [v, u_forkant, u_bakkant], rudder_bot [u, v]
  window    vinduets ytre ramme: forreste og bakerste punkt (haandlest 4x)
  masks     kolonner/rader som er skjult (stoetter, klosser, stropper)

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 --lock -- python n4_trace.py
"""
import numpy as np
from PIL import Image

import common as c

IMG = r"C:/Users/stig/Documents/Seilbåt/nye_2026-11-13/nye (4).jpeg"
A = np.asarray(Image.open(IMG).convert("RGB")).astype(float)
H_, W_ = A.shape[:2]
R, G, B = A[..., 0], A[..., 1], A[..., 2]
Y = A.mean(axis=2)
MAG = R - 0.5 * (G + B)          # bunnstoff: lyst (130, 38, 38) -> 92, i skygge (46, 18, 17) -> 28; asfalt ~ 8
BR = B - R                        # himmel/presenning > 30, kremhvitt skrog -30..-45


def smooth(a, k=3):
    if k <= 1:
        return a
    w = np.ones(k) / k
    return np.convolve(np.pad(a, (k // 2, k // 2), mode="edge"), w, mode="valid")


def cross(prof, lo_val, hi_val, start, step):
    """Foerste (subpiksel) indeks fra start i retning step der prof krysser midt
    mellom lo_val og hi_val. hi_val er verdien paa START-siden."""
    thr = 0.5 * (lo_val + hi_val)
    s = np.sign(hi_val - lo_val)
    i = int(start)
    n = len(prof)
    while 0 <= i + step < n and 0 <= i:
        a, b = prof[i], prof[i + step]
        if (a - thr) * s >= 0 > (b - thr) * s:
            t = (a - thr) / (a - b)
            return i + step * t
        i += step
    return np.nan


def robust_keep(x, y, deg, k=3.0, floor=1.0, it=3):
    keep = np.ones(len(x), bool)
    for _ in range(it):
        cf = np.polyfit(x[keep], y[keep], deg)
        r = y - np.polyval(cf, x)
        s = 1.4826 * np.median(np.abs(r[keep]))
        keep = np.abs(r) < max(k * s, floor)
    return keep


# ---------------------------------------------------------------- fenderlisten
STRAKE_G = [(40, 336.0), (120, 342.5), (200, 350.0), (300, 360.5), (400, 371.5), (500, 381.5), (600, 391.0),
            (700, 400.5), (800, 410.0), (900, 419.5), (960, 424.0), (1000, 426.0), (1018, 427.5)]


def trace_strake():
    g = np.asarray(STRAKE_G, float)
    out = []
    for u in range(44, 1017):
        vg = np.interp(u, g[:, 0], g[:, 1])
        r0 = int(round(vg)) - 12
        prof = Y[r0:r0 + 25, u]
        i = int(np.argmin(prof[6:19])) + 6
        bg_top = np.median(prof[:4])
        bg_bot = np.median(prof[-4:])
        mn = prof[i]
        if min(bg_top, bg_bot) - mn < 40:
            continue
        top = cross(prof, bg_top, mn, i, -1)
        bot = cross(prof, bg_bot, mn, i, +1)
        if not (np.isfinite(top) and np.isfinite(bot)):
            continue
        w = bot - top
        if w < 3.0 or w > 10.0:
            continue
        out.append((u, r0 + top, r0 + bot, r0 + 0.5 * (top + bot), w))
    out = np.array(out)
    keep = robust_keep(out[:, 0], out[:, 3], 5, floor=0.8)
    wmed = np.median(out[keep, 4])
    keep &= np.abs(out[:, 4] - wmed) < 2.0
    return out[keep]


# ---------------------------------------------------------------- stevnen
def trace_stem(v0=380, v1=469):
    """Ytterste lyse kant per rad. Leter fra venstre mot hoeyre fra en grov
    linje minus 14 px; kanten er der Y krysser midt mellom bakgrunnen
    (median av 4 px til venstre) og skroget (220)."""
    out = []
    for v in range(v0, v1):
        ug = 60.0 + 1.0 * (v - 382.0)
        a = int(ug) - 14
        prof = smooth(Y[v, :], 1)
        seg = prof[a:a + 30]
        j = np.where(seg > 195)[0]
        if len(j) == 0:
            continue
        j0 = a + j[0]
        if np.median(prof[j0:j0 + 5]) < 205:
            continue
        hull = np.median(prof[j0 + 1:j0 + 6])
        bg = np.median(prof[j0 - 6:j0 - 2])
        if hull - bg < 60:
            continue
        x = cross(prof, bg, hull, j0 + 1, -1)
        if np.isfinite(x):
            out.append((v, x))
    out = np.array(out)
    k = robust_keep(out[:, 0], out[:, 1], 2, floor=1.0)
    return out[k]


def trace_crease(stem):
    """Den tynne morke linja innenfor stevnkanten: minimum av Y 12-28 px
    innenfor, subpiksel med parabel."""
    out = []
    for v, us in stem:
        v = int(v)
        a = int(us) + 10
        prof = smooth(Y[v, :], 3)
        seg = prof[a:a + 20]
        i = int(np.argmin(seg))
        if i in (0, len(seg) - 1):
            continue
        depth = np.median(Y[v, a + 22:a + 28]) - seg[i]
        if depth < 6:
            continue
        y0, y1, y2 = seg[i - 1], seg[i], seg[i + 1]
        den = y0 - 2 * y1 + y2
        d = 0.5 * (y0 - y2) / den if den > 1e-6 else 0.0
        out.append((v, a + i + d))
    out = np.array(out)
    k = robust_keep(out[:, 0], out[:, 1], 1, floor=1.0)
    return out[k]


def trace_stem_hi(v0=338, v1=377):
    """Rad 338-376: ytterste lyse kant (krem mot bakgrunn), fra en grov linje
    u = 42 + 0.85 (v - 340)."""
    out = []
    for v in range(v0, v1):
        ug = 42.0 + 0.85 * (v - 340.0)
        a = int(ug) - 8
        prof = Y[v, :]
        seg = prof[a:a + 20]
        j = np.where(seg > 195)[0]
        if len(j) == 0:
            continue
        j0 = a + j[0]
        hull = np.median(prof[j0 + 1:j0 + 5])
        bg = np.median(prof[j0 - 5:j0 - 1])
        if hull - bg < 50 or hull < 205:
            continue
        x = cross(prof, bg, hull, j0 + 1, -1)
        if np.isfinite(x):
            out.append((v, x))
    out = np.array(out)
    k = robust_keep(out[:, 0], out[:, 1], 1, floor=1.0)
    return out[k]


# ---------------------------------------------------------------- overkanten ved baugen
SHEER_SKIP = [(128.0, 156.0), (192.0, 210.0), (380.0, 400.0)]     # pulpit-foten, rekkestoetter


def trace_sheer(u0=60, u1=400):
    """Skrogets overkant: oeverste rad der kremhvitt (B - R < -20, Y > 200)
    begynner, leter oppover fra raden under listen. Subpiksel paa B - R."""
    out = []
    for u in range(u0, u1):
        if any(a <= u <= b for a, b in SHEER_SKIP):
            continue
        vs = 0.5 * (318.0 + (u - 100.0) * (336.0 - 318.0) / 300.0)
        vg = 318.0 + (u - 100.0) * (336.0 - 318.0) / 300.0
        v = int(vg) + 8
        while v > vg - 14 and BR[v, u] < -20 and Y[v, u] > 200:
            v -= 1
        if v <= vg - 14:
            continue
        prof = BR[:, u]
        cream = np.median(prof[v + 2:v + 6])
        above = np.median(prof[v - 3:v + 1])
        x = cross(prof, above, cream, v + 2, -1)
        if np.isfinite(x):
            out.append((u, x))
    out = np.array(out)
    k = robust_keep(out[:, 0], out[:, 1], 2, floor=1.0)
    return out[k]


# ---------------------------------------------------------------- hekken
def trace_stern(v0=396, v1=497):
    """Akterste kant per rad: kremhvitt skrog mot den blaa presenningen
    (B - R stiger kraftig). Leter fra en grov kurve mot hoeyre."""
    gv = np.array([396, 410, 420, 428, 440, 456, 470, 484, 496], float)
    gu = np.array([1004, 1012, 1016, 1018, 1016, 1012, 1005, 995, 978], float)
    out = []
    for v in range(v0, v1):
        ug = np.interp(v, gv, gu)
        a = int(ug) - 14
        prof = smooth(BR[v, :], 1)
        seg = prof[a:a + 28]
        j = np.where(seg > 20)[0]
        if len(j) == 0:
            continue
        j0 = a + j[0]
        hull = np.median(prof[j0 - 7:j0 - 2])
        bg = np.median(prof[j0 + 1:j0 + 5])
        if bg - hull < 50:
            continue
        x = cross(prof, bg, hull, j0 - 2, +1)
        if np.isfinite(x):
            out.append((v, x))
    out = np.array(out)
    k = robust_keep(out[:, 0], out[:, 1], 4, floor=1.0)
    return out[k]


def trace_stem_wl():
    """Vaar stevn ved stripen: rad 470-477 foerste kremhvite piksel (Y > 180)
    fra venstre etter den andre baatens blaa; rad 483-497 foerste moerkblaa
    piksel (B > R + 5, Y < 90) etter dens hvite/roede stripe."""
    out = []
    for v in range(470, 478):
        prof = Y[v, :]
        a = 150
        j = np.where(prof[a:a + 30] > 180)[0]
        if len(j) == 0 or prof[a + j[0] - 3] > 150:
            continue
        j0 = a + j[0]
        x = cross(prof, np.median(prof[j0 - 6:j0 - 2]), np.median(prof[j0 + 1:j0 + 5]), j0 + 1, -1)
        if np.isfinite(x):
            out.append((v, x))
    for v in range(483, 498):
        ug = 173.0 + (v - 484.0)
        a = int(ug) - 8
        navy = (BR[v, a:a + 20] > 5) & (Y[v, a:a + 20] < 90)
        j = np.where(navy)[0]
        if len(j) < 3:
            continue
        j0 = a + j[0]
        prof = BR[v, :]
        x = cross(prof, np.median(prof[j0 - 6:j0 - 2]), np.median(prof[j0 + 1:j0 + 4]), j0 + 1, -1)
        if np.isfinite(x):
            out.append((v, x))
    return np.array(out)


# listens akterende (haandlest 6x): den morke listen stikker ut av hekkens
# omriss, akterste punkt midt i listen
STRAKE_END = [1019.0, 427.5]


# ---------------------------------------------------------------- vannlinjestripen
def trace_boottop(u0=150, u1=990):
    """Per kolonne: blaa overkant (krem -> moerk blaa), blaa underkant (blaa ->
    hvit tynn stripe) og roedt start (hvit stripe -> roedt)."""
    out = []
    for u in range(u0, u1):
        vg = 478.5 + (u - 200.0) * (494.5 - 478.5) / 700.0
        r0 = int(vg) - 12
        cy = Y[r0:r0 + 40, u]
        dark = np.where(cy[:30] < 110)[0]
        if len(dark) < 8:
            out.append((u, np.nan, np.nan, np.nan))
            continue
        b0 = dark[0]
        if b0 < 4:
            out.append((u, np.nan, np.nan, np.nan))
            continue
        cream = np.median(cy[max(b0 - 6, 0):b0 - 1])
        blue = np.median(cy[b0 + 3:b0 + 12])
        top = cross(cy, blue, cream, b0 - 1, +1) if cream - blue > 60 else np.nan
        # hvit stripe: foerste lyse topp under det blaa
        j = b0 + 8 + int(np.argmax(cy[b0 + 8:b0 + 26]))
        white = cy[j]
        if white - blue < 50:
            out.append((u, r0 + top, np.nan, np.nan))
            continue
        bot_blue = cross(cy, blue, white, j, -1)
        red = np.median(cy[j + 3:j + 7])
        mred = np.median(MAG[r0 + j + 3:r0 + j + 7, u])
        red_c = cross(cy, red, white, j, +1) if (mred > 25 and white - red > 50) else np.nan
        out.append((u, r0 + top, r0 + bot_blue, r0 + red_c))
    out = np.array(out, float)
    # ut med enkeltkolonner der kanten hoppet til en annen kant (skruer, merker)
    for j in (1, 2, 3):
        ok = np.isfinite(out[:, j])
        keep = robust_keep(out[ok, 0], out[ok, j], 3, floor=0.8)
        col = out[:, j].copy()
        idx = np.where(ok)[0]
        col[idx[~keep]] = np.nan
        out[:, j] = col
    return out


# ---------------------------------------------------------------- roedt omriss
def is_red(v, u):
    return MAG[v, u] > 18.0


def red_edge_down(u, v_lo, v_hi, run=4, thr=18.0):
    """Nederste roede rad i kolonne u: leter OPPOVER fra v_hi til et loep paa
    minst run roede piksler, saa subpiksel paa Y (moerkt bunnstoff mot lysere
    asfalt) eller paa MAG der Y-kontrasten er svak."""
    vs = np.arange(v_lo, v_hi)
    red = MAG[vs, u] > thr
    k = len(vs) - 1
    while k >= run:
        if red[k - run + 1:k + 1].all():
            last = vs[k]
            py = smooth(Y[:, u], 1)
            pm = smooth(MAG[:, u], 1)
            yin, yout = np.median(py[last - 6:last - 1]), np.median(py[last + 3:last + 8])
            if abs(yout - yin) > 25:
                return cross(py, yout, yin, last - 2, +1)
            return cross(pm, np.median(pm[last + 3:last + 8]), np.median(pm[last - 6:last - 1]), last - 2, +1)
        k -= 1
    return np.nan


def red_edge_row(v, u_lo, u_hi, side, run=4, thr=18.0):
    """Roedt omriss i rad v: side -1 = venstre kant (min u), +1 = hoeyre kant.
    Subpiksel paa MAG."""
    us = np.arange(u_lo, u_hi)
    red = MAG[v, us] > thr
    prof = smooth(MAG[v, :], 1)
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


# skjulte kolonner for bunnens omriss (stoetter, hjul bak, klosser)
BOTTOM_MASK = [(352.0, 362.0),     # den fremre rustne stoetten: bena (mellom dem: trace_bottom_dark)
               (362.0, 378.0),
               (378.0, 398.0),
               (418.0, 568.0),     # roed kile bak skroget + den rustne stoetten med armen (se rapporten)
               (776.0, 790.0),     # kjolens bakkant og stroppen
               (806.0, 846.0)]     # soelvstoettens topp


def masked(u, mask):
    return any(a <= u <= b for a, b in mask)


BOTTOM_RANGES = [(170, 546)]      # foran kjolen (akter for kjolen er bakgrunnen moerk blaa: ikke sporbar)


def trace_bottom():
    out = []
    for u in [u for a, b in BOTTOM_RANGES for u in range(a, b)]:
        if masked(u, BOTTOM_MASK):
            continue
        y = red_edge_down(u, 496 if u < 260 else 520, 600)
        if np.isfinite(y):
            out.append((u, y))
    return np.array(out)


# kolonner der bakgrunnen ogsaa er roed/brun (stoettens tverrjern, den roede
# kilen bak): kanten der Y stiger fra skrogets moerke underside
DARK_RANGES = [(363, 378), (420, 446)]


def trace_bottom_dark():
    out = []
    for u in [u for a, b in DARK_RANGES for u in range(a, b)]:
        prof = smooth(Y[:, u], 1)
        hull = np.median(prof[553:560])
        v = 558
        while v < 580 and prof[v] < hull + 15:
            v += 1
        if v >= 580:
            continue
        below = np.median(prof[v + 2:v + 6])
        if below - hull < 25:
            continue
        x = cross(prof, below, hull, v - 3, +1)
        if np.isfinite(x):
            out.append((u, x))
    return np.array(out)


def trace_front(v0=514, v1=566):
    """Forfotens forkant per rad: stripen (moerk blaa/hvit) og bunnstoffet mot
    asfalten. Over det roede brukes avstand i farge fra skroget like innenfor;
    i det roede MAG-kanten."""
    out = []
    for v in range(v0, v1):
        ug = 142.0 + (v - 472.0) * 1.6 if v < 520 else 219.0 + (v - 520.0) * 3.2
        lo, hi = int(ug) - 25, int(ug) + 60
        x = red_edge_row(v, lo, hi, -1, run=4, thr=22.0)
        if np.isfinite(x):
            out.append((v, x, 1.0))
            continue
        # stripen: krem/blaa/hvit mot bakgrunn, fargeavstand fra skroget 4-8 px innenfor
        prof = Y[v, :]
        seg = prof[lo:hi]
        j = np.where(np.abs(np.diff(seg)) > 30)[0]
        if len(j) == 0:
            continue
        out.append((v, lo + j[0] + 0.5, 0.0))
    return np.array(out)


def trace_keel():
    le, te, bot = [], [], []
    for v in range(578, 680):
        x = red_edge_row(v, 540, 700, -1, thr=40.0)
        if np.isfinite(x):
            le.append((v, x))
    for v in range(580, 672):
        x = red_edge_row(v, 700, 800, +1, thr=40.0)
        if np.isfinite(x):
            te.append((v, x))
    te = np.array(te)
    te = te[robust_keep(te[:, 0], te[:, 1], 2, floor=1.0)]          # stroppen krysser ved rad ~605
    for u in range(640, 776):
        if masked(u, KEEL_BOT_MASK):
            continue
        y = red_edge_down(u, 640, 700, thr=40.0)
        if np.isfinite(y):
            bot.append((u, y))
    return np.array(le), te, np.array(bot)


KEEL_BOT_MASK = [(690.0, 724.0), (733.0, 764.0)]      # klossene under kjolen


def trace_rudder():
    out, bot = [], []
    for v in range(556, 604):
        a = red_edge_row(v, 900, 990, -1, thr=25.0)
        b = red_edge_row(v, 900, 990, +1, thr=25.0)
        if np.isfinite(a) and np.isfinite(b):
            out.append((v, a, b))
    for u in range(935, 972):
        y = red_edge_down(u, 560, 625, thr=25.0)
        if np.isfinite(y):
            bot.append((u, y))
    return np.array(out), np.array(bot)


# vinduets ytre ramme (haandlest paa 10x): rund forende midt i hoeyden
# (rammen v 366,5-393), akterenden skraa med bakerste punkt naer underkanten.
# Rammens underkant ligger rett paa listens overkant (0-1 px glipe; modellen
# har WIN_ABOVE_STRAKE 70 = ca. 6 px)
WINDOW = dict(fwd_end=[651.0, 380.0], aft_end=[832.5, 402.0])


if __name__ == "__main__":
    st = trace_strake()
    sm = trace_stem()
    cr = trace_crease(sm)
    sh = trace_stem_hi()
    swl = trace_stem_wl()
    she = trace_sheer()
    ste = trace_stern()
    bt = trace_boottop()
    bo = trace_bottom()
    bd = trace_bottom_dark()
    fr = trace_front()
    kle, kte, kbo = trace_keel()
    ru, rb = trace_rudder()
    print("stem_wl %d" % len(swl))
    print("strake %d (u %.0f-%.0f), stem %d, crease %d, stem_hi %d, sheer %d, stern %d, boottop %d (blaa %d, roedt %d)"
          % (len(st), st[0, 0], st[-1, 0], len(sm), len(cr), len(sh), len(she), len(ste), len(bt),
             np.isfinite(bt[:, 2]).sum(), np.isfinite(bt[:, 3]).sum()))
    print("bottom_dark %d" % len(bd))
    print("bottom %d, front %d, keel le %d te %d bot %d, rudder %d bot %d"
          % (len(bo), len(fr), len(kle), len(kte), len(kbo), len(ru), len(rb)))
    out = dict(image="nye (4).jpeg (1170 x 831)", W=W_, H=H_, strake=st[:, :4], stem=sm, crease=cr, stem_hi=sh, stem_wl=swl,
               sheer=she, stern=ste, strake_end=STRAKE_END, boottop=bt, bottom=bo, bottom_dark=bd, front=fr, keel_le=kle,
               keel_te=kte, keel_bot=kbo, rudder=ru, rudder_bot=rb, window=WINDOW,
               masks=dict(bottom=BOTTOM_MASK, keel_bot=KEEL_BOT_MASK, sheer=SHEER_SKIP))
    c.save_json(out, c.W + "/out/n4_trace.json")
