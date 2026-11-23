"""Sporing i IMG_9374 (babord side, baaten henger i stroppene, 761 x 472).

Bildet er et lite utsnitt/skjermklipp (originalen i ~/Documents/Seilbaat er
like stor). Alle punkter er (u, v) i bildets piksler, u mot hoeyre, v nedover,
origo oppe til venstre, piksel-senter som i PIL (u = kolonneindeks).

Lager ../out/t9374_cam.json (linjer til kameraet, ting trinn 5 ikke endrer)
og ../out/t9374_raw.json (forkroppens omriss, foer kjol-utvalget i fk9374.py):
  strake    fenderlistens senter per kolonne [u, v_top, v_bot, v_mid]
  stem      stevnens forkant per rad over z ~ +300 [v, u] (hvitt skrog mot
            traer/bakgrunn; rader der stroppen og stolpen bak krysser er ute)
  boottop   per kolonne [u, v_blaa_overkant, v_blaa_underkant, v_lys_stripe,
            v_roedt_start] (NaN der ikke funnet)
  window    vinduets ytre ramme: forreste punkt og bakerste punkt (haandlest
            paa 4x forstoerrelse, +-1 px)
  keel_le   kjolens forkant per rad [v, u] (roedt mot vann)
  keel_te   kjolens bakkant per rad [v, u]
  keel_bot  kjolens bunn per kolonne [u, v]
  front     forkroppens forkant per rad (stevn/forfot under z ~ +300) [v, u]
  bottom    forkroppens nedre omriss per kolonne [u, v] (roedt mot bakgrunn)
  aft_bot   skrogets nedre omriss akter for kjolen (kontroll) [u, v]
  rudder    det roede bladet ved u 674-686 [v, u_min, u_max]

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python t9374.py
"""
import json

import numpy as np
from PIL import Image

import common as c

IMG = r"C:/Users/stig/Documents/Seilbåt/IMG_9374.jpeg"
A = np.asarray(Image.open(IMG).convert("RGB")).astype(float)
H_, W_ = A.shape[:2]
R, G, B = A[..., 0], A[..., 1], A[..., 2]
Y = A.mean(axis=2)
MAG = 0.5 * (R + B) - G          # bunnstoffet er mork vinroed: (62, 28, 53) -> ca. 30
BLU = B - R


def smooth(a, k=3):
    if k <= 1:
        return a
    w = np.ones(k) / k
    return np.convolve(np.pad(a, (k // 2, k // 2), mode="edge"), w, mode="valid")


def guide(pts, u):
    p = np.asarray(pts, float)
    return np.interp(u, p[:, 0], p[:, 1])


def cross(prof, lo_val, hi_val, start, step):
    """Foerste (subpiksel) indeks fra start i retning step der prof krysser midt
    mellom lo_val og hi_val. hi_val er verdien paa START-siden (den trenger
    ikke vaere stoerst), lo_val verdien paa den andre siden."""
    thr = 0.5 * (lo_val + hi_val)
    s = np.sign(hi_val - lo_val)
    i = start
    n = len(prof)
    while 0 <= i + step < n and 0 <= i:
        a, b = prof[i], prof[i + step]
        if (a - thr) * s >= 0 > (b - thr) * s:
            t = (a - thr) / (a - b)
            return i + step * t
        i += step
    return np.nan


# ---------------------------------------------------------------- fenderlisten
STRAKE_G = [(22, 117), (60, 122), (90, 126), (120, 129), (150, 133), (180, 136.5), (210, 140.5), (240, 144.5),
            (270, 148.5), (300, 152.5), (330, 156), (360, 160), (390, 164), (420, 168), (450, 171),
            (480, 174.5), (510, 178.5), (540, 182), (570, 185), (600, 189), (630, 192), (690, 198.5), (705, 200)]


def trace_strake():
    out = []
    for u in range(26, 704):
        g = guide(STRAKE_G, u)
        r0 = int(round(g)) - 14
        prof = smooth(Y[r0:r0 + 29, u], 1)
        i = int(np.argmin(prof[8:21])) + 8
        bg_top = np.median(prof[:4])
        bg_bot = np.median(prof[-4:])
        mn = prof[i]
        if min(bg_top, bg_bot) - mn < 35:
            continue
        top = cross(prof, bg_top, mn, i, -1)
        bot = cross(prof, bg_bot, mn, i, +1)
        if not (np.isfinite(top) and np.isfinite(bot)):
            continue
        w = bot - top
        if w < 3.0 or w > 11.0:
            continue
        out.append((u, r0 + top, r0 + bot, r0 + 0.5 * (top + bot), w))
    out = np.array(out)
    # stropper og annet: ut det som avviker fra en glatt kurve eller er for bredt
    keep = np.ones(len(out), bool)
    for _ in range(3):
        cf = np.polyfit(out[keep, 0], out[keep, 3], 4)
        r = out[:, 3] - np.polyval(cf, out[:, 0])
        s = 1.4826 * np.median(np.abs(r[keep]))
        keep = np.abs(r) < max(3 * s, 1.0)
    wmed = np.median(out[keep, 4])
    keep &= np.abs(out[:, 4] - wmed) < 2.5
    return out[keep]


# ---------------------------------------------------------------- stevnen over z ~ +300
def trace_stem(v0=121, v1=236):
    """Hvitt skrog mot bakgrunn: per rad, kanten der Y stiger fra bakgrunnen
    til skrogsiden (leter fra venstre mot en grov linje)."""
    out = []
    for v in range(v0, v1):
        ug = 25.0 + 0.886 * (v - 120.0)
        a = int(ug) - 12
        prof = smooth(Y[v, a:a + 25], 1)
        hull = np.median(Y[v, int(ug) + 6:int(ug) + 12])
        bg = np.median(Y[v, int(ug) - 12:int(ug) - 6])
        if hull - bg < 50:
            continue
        x = cross(prof, bg, hull, 24, -1)       # fra skroget mot venstre
        if np.isfinite(x):
            out.append((v, a + x))
    out = np.array(out)
    k = np.polyfit(out[:, 0], out[:, 1], 1)
    r = out[:, 1] - np.polyval(k, out[:, 0])
    m = np.abs(r) < 1.5
    k = np.polyfit(out[m, 0], out[m, 1], 1)
    r = out[:, 1] - np.polyval(k, out[:, 0])
    return out[np.abs(r) < 1.2]


# ---------------------------------------------------------------- vannlinjestripen
def trace_boottop():
    """Per kolonne: blaa overkant (hvit -> blaa), blaa underkant (blaa -> lys
    stripe), lys stripe (maks Y), roedt start (lys stripe -> roedt)."""
    out = []
    for u in range(146, 704):
        g = 252.0 + (u - 146.0) * (268.0 - 252.0) / (700.0 - 146.0)
        r0 = int(g) - 14
        cb = smooth(BLU[r0:r0 + 40, u], 1)
        cy = smooth(Y[r0:r0 + 40, u], 1)
        cm = smooth(MAG[r0:r0 + 40, u], 1)
        isb = (cb > 15) & (cy < 90)
        if isb.sum() < 4:
            continue
        idx = np.where(isb)[0]
        runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
        run = max(runs, key=len)
        if len(run) < 4:
            continue
        b0, b1 = run[0], run[-1]
        if b0 < 3:
            continue
        white = np.median(cy[max(b0 - 6, 0):b0 - 1])
        blue = np.median(cy[b0 + 1:b1])
        top = cross(cy, white, blue, b0 + 1, -1)
        # lys stripe under det blaa
        j = int(np.argmax(cy[b1:b1 + 6])) + b1
        ycream = cy[j]
        if ycream - blue < 20:
            out.append((u, r0 + top, np.nan, np.nan, np.nan))
            continue
        bot_blue = cross(cy, blue, ycream, j, -1)
        red = np.median(cy[j + 3:j + 7])
        if np.median(cm[j + 3:j + 7]) < 12:
            red_c = np.nan
        else:
            red_c = cross(cy, red, ycream, j, +1)
        out.append((u, r0 + top, r0 + bot_blue, r0 + j, r0 + red_c))
    return np.array(out, float)


# ---------------------------------------------------------------- roedt omriss
def is_red(v, u):
    return MAG[v, u] > 14.0


def red_edge_down(u, v_lo, v_hi, run=4):
    """Nederste roede rad i kolonne u: leter OPPOVER fra v_hi (bakgrunn) til et
    loep paa minst run roede piksler, saa subpiksel paa MAG."""
    vs = np.arange(v_lo, v_hi)
    red = MAG[vs, u] > 14.0
    k = len(vs) - 1
    while k >= run:
        if red[k - run + 1:k + 1].all():
            last = vs[k]
            prof = smooth(MAG[:, u], 1)
            inside = np.median(prof[last - 6:last - 1])
            outside = np.median(prof[last + 3:last + 8])
            return cross(prof, outside, inside, last - 2, +1)
        k -= 1
    return np.nan


def red_edge_row(v, u_lo, u_hi, side, run=4):
    """Roedt omriss i rad v: side -1 = venstre kant (min u), +1 = hoeyre kant."""
    us = np.arange(u_lo, u_hi)
    red = MAG[v, us] > 14.0
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


def trace_keel():
    le, te, bot = [], [], []
    for v in range(340, 416):
        x = red_edge_row(v, 395, 560, -1)
        if np.isfinite(x):
            le.append((v, x))
    for v in range(345, 404):
        x = red_edge_row(v, 520, 596, +1)
        if np.isfinite(x):
            te.append((v, x))
    for u in range(470, 586):
        y = red_edge_down(u, 380, 432)
        if np.isfinite(y):
            bot.append((u, y))
    return np.array(le), np.array(te), np.array(bot)


def trace_front(v0=232, v1=306):
    """Forkroppens forkant per rad, fra z ~ +300 ned til forfoten flater ut.
    Over det roede (stripen og hvitt) brukes skrog-mot-bakgrunn paa
    fargeavstand; i det roede MAG-kanten."""
    out = []
    for v in range(v0, v1):
        ug = 25.0 + 0.886 * (v - 120.0)
        if v >= 271:
            x = red_edge_row(v, int(ug) - 10, int(ug) + 80, -1)
            if np.isfinite(x):
                out.append((v, x, 1.0))
            continue
        # over roedt: skrogets farge til hoeyre for kanten mot bakgrunnen
        a = int(ug) - 10
        seg = A[v, a:a + 22]
        hull = np.median(A[v, int(ug) + 5:int(ug) + 10], axis=0)
        d = np.linalg.norm(seg - hull, axis=1)
        d = smooth(d, 1)
        dbg = np.median(d[:5])
        if dbg < 40:
            continue
        x = cross(d, dbg, 0.0, 21, -1)
        if np.isfinite(x):
            out.append((v, a + x, 0.0))
    return np.array(out)


def trace_bottom(u0=163, u1=470):
    out = []
    for u in range(u0, u1):
        y = red_edge_down(u, 262, 372)
        if np.isfinite(y):
            out.append((u, y))
    return np.array(out)


def trace_aft_bottom(u0=586, u1=690):
    out = []
    for u in range(u0, u1):
        y = red_edge_down(u, 262, 300 if u > 672 else 372)
        if np.isfinite(y):
            out.append((u, y))
    return np.array(out)


def trace_rudder():
    out = []
    for v in range(300, 348):
        a = red_edge_row(v, 664, 700, -1)
        b = red_edge_row(v, 664, 700, +1)
        if np.isfinite(a) and np.isfinite(b):
            out.append((v, a, b))
    return np.array(out)


# vinduets ytre ramme (haandlest paa 4x, IMG_9374): rund forende midt i
# hoeyden, akterenden skraa med bakerste punkt naer underkanten
WINDOW = dict(fwd_end=[540.5, 170.0], aft_end=[652.0, 185.5])

# stropper og ting som skjuler omrisset (u-intervaller, per rad/kolonne):
SLING_COLS_BOTTOM = [(396.0, 422.0)]      # fremre stropp krysser bunnen ved u ~ 400-412
SLING_COLS_AFT = [(596.0, 650.0)]         # propell/brakett og bakre stropp


if __name__ == "__main__":
    st = trace_strake()
    sm = trace_stem()
    bt = trace_boottop()
    kle, kte, kbo = trace_keel()
    fr = trace_front()
    bo = trace_bottom()
    ab = trace_aft_bottom()
    ru = trace_rudder()
    print("strake %d, stem %d, boottop %d (roedt %d), keel le %d te %d bot %d, front %d, bottom %d, aft %d, rudder %d"
          % (len(st), len(sm), len(bt), np.isfinite(bt[:, 4]).sum(), len(kle), len(kte), len(kbo), len(fr),
             len(bo), len(ab), len(ru)))
    cam = dict(image="IMG_9374 (761 x 472)", strake=st[:, :4], stem=sm, boottop=bt, window=WINDOW,
               keel_le=kle, keel_te=kte, keel_bot=kbo, aft_bot=ab, rudder=ru,
               desc=dict(strake="[u, v_top, v_bot, v_mid] fenderlistens morke band per kolonne",
                         stem="[v, u] stevnens forkant (hvitt skrog mot bakgrunn), rad 121-235",
                         boottop="[u, v_blaa_overkant, v_blaa_underkant, v_lys_stripe_maks, v_roedt_start]",
                         window="vinduets ytre ramme: forreste og bakerste punkt (u, v)",
                         keel_le="[v, u] kjolens forkant (roedt mot vann)",
                         keel_te="[v, u] kjolens bakkant",
                         keel_bot="[u, v] kjolens bunn",
                         aft_bot="[u, v] skrogets nedre omriss akter for kjolen (kontroll)",
                         rudder="[v, u_min, u_max] det roede bladet ved u 674-686"))
    c.save_json(cam, c.W + "/out/t9374_cam.json")
    raw = dict(front=fr, bottom=bo, boottop=bt, sling_cols_bottom=SLING_COLS_BOTTOM)
    c.save_json(raw, c.W + "/out/t9374_raw.json")
