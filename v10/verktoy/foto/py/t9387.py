"""Sporing i IMG_9387 (babord side paa land, naert hold, 2000 x 1500).

Lager ../out/t9387_cam.json; forkroppen spores med funksjonene her fra
fk9387.py (som trenger kameraet for aa luke bort kjolens del).
  t9387_cam.json      linjer til kameraet (ting trinn 5 ikke endrer):
                      fenderlisten, dekkskanten (silhuett), vannlinjestripen,
                      vinduets ender, akterspeilets hjoerne (silhuett), kjolen,
                      roret og stevnen over ca. z +260
  t9387_forkropp.json forkroppen under vann foran kjolen: omrisset av det roede
                      (stevn/forfot per rad, bunn per kolonne) og nedre kant av
                      den lyse stripen (overgangen til roedt, z ca. +38)

Alle punkter er (u, v) i bildets piksler, u mot hoeyre, v nedover, origo oppe
til venstre, piksel-senter-konvensjon som i PIL (u = kolonneindeks).
Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python t9387.py
"""
import json

import numpy as np
from PIL import Image

import common as c

IMG = c.FOTO + "/IMG_9387.jpg"
A = np.asarray(Image.open(IMG).convert("RGB")).astype(float)
H_, W_ = A.shape[:2]
R, G, B = A[..., 0], A[..., 1], A[..., 2]
Y = A.mean(axis=2)
RED = R - np.maximum(G, B)          # roedhet
BLU = B - R                          # blaahet


def guide(pts, u):
    p = np.asarray(pts, float)
    return np.interp(u, p[:, 0], p[:, 1])


def smooth(a, k=3):
    if k <= 1:
        return a
    w = np.ones(k) / k
    return np.convolve(np.pad(a, (k // 2, k // 2), mode="edge"), w, mode="valid")


def cross(prof, lo_val, hi_val, start, step):
    """Foerste indeks (subpiksel) fra start i retning step der prof krysser
    midt mellom lo_val og hi_val. prof antas aa gaa fra naer hi_val til lo_val."""
    thr = 0.5 * (lo_val + hi_val)
    n = len(prof)
    i = start
    s = np.sign(hi_val - lo_val)
    while 0 <= i + step < n:
        a, b = prof[i], prof[i + step]
        if (a - thr) * s >= 0 > (b - thr) * s:
            t = (a - thr) / (a - b)
            return i + step * t
        i += step
    return np.nan


# ---------------------------------------------------------------- fenderlisten
STRAKE_G = [(0, 125), (100, 140), (500, 208), (1000, 298), (1300, 352),
            (1500, 393), (1680, 434), (1760, 462), (1815, 486)]


def trace_strake():
    out = []
    for u in range(2, 1812, 4):
        g = guide(STRAKE_G, u)
        r0 = int(g - 32)
        prof = smooth(Y[r0:r0 + 65, u], 3)
        i = int(np.argmin(prof[16:49])) + 16
        bg = np.median(np.r_[prof[:6], prof[-6:]])
        mn = prof[i]
        if bg - mn < 40:
            continue
        top = cross(prof, bg, mn, i, -1)
        bot = cross(prof, bg, mn, i, +1)
        if not (np.isfinite(top) and np.isfinite(bot)):
            continue
        w = bot - top
        if w < 5 or w > 30:
            continue
        out.append((u, r0 + top, r0 + bot, r0 + 0.5 * (top + bot)))
    return np.array(out)


# ---------------------------------------------------------------- vannlinjestripen
def trace_boottop():
    """Per kolonne: blaa overkant (hvit -> blaa), blaa underkant (blaa -> lys
    stripe) og lys stripes underkant (lys -> roedt)."""
    out = []
    for u in range(80, 1722, 3):
        col_b = smooth(BLU[:, u], 3)
        col_y = smooth(Y[:, u], 3)
        col_r = smooth(RED[:, u], 3)
        # stripen ligger mellom rad 530 og 650
        seg = np.arange(520, 660)
        isb = col_b[seg] > 18
        if isb.sum() < 8:
            continue
        rb = seg[isb]
        # lengste sammenhengende blaa-loep
        br = np.split(rb, np.where(np.diff(rb) > 2)[0] + 1)
        run = max(br, key=len)
        if len(run) < 8:
            continue
        b0, b1 = run[0], run[-1]
        blue_in = np.median(col_b[b0 + 2:b1 - 1])
        white_b = np.median(col_b[b0 - 12:b0 - 4])
        top = cross(col_b, white_b, blue_in, b0 + 2, -1)
        # under det blaa: lys stripe (hoey Y), saa roedt (hoey RED)
        yb = np.median(col_y[b1 - 6:b1 - 1])
        k = b1
        ymax_i = int(np.argmax(col_y[b1:b1 + 14])) + b1
        ycream = col_y[ymax_i]
        if ycream - yb < 25:
            out.append((u, top, b1, np.nan, np.nan))
            continue
        bot_blue = cross(col_y, yb, ycream, ymax_i, -1)
        # under stripen: roedt; terskel midt mellom stripens og det roede Y
        yred = np.median(col_y[ymax_i + 8:ymax_i + 16])
        cr_red = cross(col_y, yred, ycream, ymax_i, +1)
        rr = np.median(col_r[ymax_i + 8:ymax_i + 16])
        if rr < 15:              # ikke roedt under stripen (forut for stevnen)
            cr_red = np.nan
        out.append((u, top, bot_blue, ymax_i, cr_red))
    return np.array(out, float)


# ---------------------------------------------------------------- dekkskanten
SHEER_G = [(300, 117), (500, 140), (700, 168), (900, 202), (1100, 233), (1300, 268)]


def trace_sheer(st):
    """Hvit skrogside opp til dekkskanten; over den himmel eller ting paa dekk.
    Leter oppover fra listens overkant til fargen slutter aa ligne skrogsiden."""
    out = []
    for u in range(300, 1306, 4):
        k = np.argmin(np.abs(st[:, 0] - u))
        if abs(st[k, 0] - u) > 6:
            continue
        r_top = int(st[k, 1]) - 4
        g = guide(SHEER_G, u)
        r_hi = int(g - 30)
        if r_hi >= r_top - 10:
            continue
        seg = A[r_hi:r_top, u, :]
        ref = np.median(A[r_top - 14:r_top - 4, u, :], axis=0)
        d = np.linalg.norm(smooth_rows(seg) - ref, axis=1)
        # fra bunnen og opp: foerste rad med tydelig avvik
        thr = 22.0
        j = len(d) - 1
        while j > 0 and d[j] < thr:
            j -= 1
        if j <= 1:
            continue
        # subpiksel: mellom j og j+1
        t = (d[j] - thr) / max(d[j] - d[j + 1], 1e-6)
        out.append((u, r_hi + j + t, d[j]))
    return np.array(out)


def smooth_rows(seg):
    k = np.ones(3) / 3
    return np.stack([np.convolve(np.pad(seg[:, i], 1, mode="edge"), k, mode="valid") for i in range(3)], 1)


# ---------------------------------------------------------------- roedt omriss
def is_red(r, u):
    """Bunnstoff: tydelig roedt, ogsaa i skygge (rust og asfalt er ikke)."""
    p = A[r, u]
    return (p[..., 0] > 28) & (p[..., 0] - p[..., 1] > 0.45 * p[..., 0]) & (p[..., 0] - p[..., 2] > 0.25 * p[..., 0])


def _edge(prof, last, step):
    """Subpiksel-kant: RED krysser midt mellom innsiden og utsiden rundt indeks last
    (siste roede piksel). step +1: utsiden ligger ved hoeyere indeks."""
    if step > 0:
        inside = np.median(prof[max(last - 7, 0):last - 1])
        outside = np.median(prof[last + 3:last + 9])
        return cross(prof, outside, inside, last - 2, +1)
    inside = np.median(prof[last + 2:last + 8])
    outside = np.median(prof[max(last - 8, 0):last - 2])
    return cross(prof, outside, inside, last + 2, -1)


def lowest_red(u, r_top, r_bot, run=4):
    """Nederste roede rad i kolonne u: leter OPPOVER fra r_bot (bakgrunn) til et
    loep paa minst `run` roede piksler (saa ting foran skroget lenger opp ikke
    stopper sporingen)."""
    rs = np.arange(r_top, r_bot)
    red = is_red(rs, np.full(len(rs), u))
    k = len(rs) - 1
    while k >= run:
        if red[k - run + 1:k + 1].all():
            last = rs[k]
            return _edge(smooth(RED[:, u], 3), last, +1)
        k -= 1
    return np.nan


def leftmost_red(r, u_start, u_end, run=4):
    """Venstre kant av det roede i rad r: leter mot HOEYRE fra u_end (bakgrunn)."""
    us = np.arange(u_end, u_start)
    red = is_red(np.full(len(us), r), us)
    for k in range(len(us) - run):
        if red[k:k + run].all():
            return _edge(smooth(RED[r, :], 3), us[k], -1)
    return np.nan


def rightmost_red(r, u_start, u_end, run=4):
    """Hoeyre kant av det roede i rad r: leter mot VENSTRE fra u_end (bakgrunn)."""
    us = np.arange(u_start, u_end)
    red = is_red(np.full(len(us), r), us)
    k = len(us) - 1
    while k >= run:
        if red[k - run + 1:k + 1].all():
            return _edge(smooth(RED[r, :], 3), us[k], +1)
        k -= 1
    return np.nan


def trace_forebody(bt):
    """Forkroppens omriss: stevn/forfot per rad (venstre kant av det roede) og
    bunnen per kolonne (nederste roede rad)."""
    # rad-retning: fra stripens nedre kant ved stevnen og ned til der
    # omrisset blir flatere enn 45 grader
    stem = []
    for r in range(606, 770):
        u = leftmost_red(r, 900, 60)
        if np.isfinite(u):
            stem.append((r, u))
    stem = np.array(stem)
    bot = []
    for u in range(140, 1000, 3):
        v = lowest_red(u, 600, 860)
        if np.isfinite(v):
            bot.append((u, v))
    return stem, np.array(bot)


# ---------------------------------------------------------------- kjolen
def trace_keel():
    le, te, bo = [], [], []
    for r in range(800, 1000, 2):
        u = leftmost_red(r, 1250, 900)
        if np.isfinite(u):
            le.append((r, u))
    for r in range(800, 965, 2):
        u = rightmost_red(r, 1250, 1480)
        if np.isfinite(u):
            te.append((r, u))
    for u in range(1100, 1392, 3):
        v = lowest_red(u, 900, 1080)
        if np.isfinite(v):
            bo.append((u, v))
    return np.array(le), np.array(te), np.array(bo)


# ---------------------------------------------------------------- roret
def trace_rudder():
    te, bo = [], []
    for r in range(700, 826, 2):
        u = rightmost_red(r, 1645, 1720)
        if np.isfinite(u):
            te.append((r, u))
    for u in range(1626, 1666, 2):
        v = lowest_red(u, 760, 880)
        if np.isfinite(v):
            bo.append((u, v))
    return np.array(te), np.array(bo)


# ---------------------------------------------------------------- akterspeilets hjoerne
def trace_transom():
    """Hoeyre kant av den hvite skrogsiden mot den gule baaten bak (rad 500-600):
    hvitt har hoey blaa-kanal, gult lav."""
    out = []
    for r in range(498, 606, 2):
        row = smooth(B[r, :], 3)
        seg = row[1700:1880]
        inside = np.median(row[1700:1712])
        # foerste fall under midt mellom hvitt og gult
        j = None
        for k in range(len(seg) - 1):
            if seg[k] > 0.5 * (inside + 60) >= seg[k + 1]:
                j = k
                break
        if j is None:
            continue
        thr = 0.5 * (inside + 60)
        t = (seg[j] - thr) / max(seg[j] - seg[j + 1], 1e-6)
        out.append((r, 1700 + j + t))
    return np.array(out)


# ---------------------------------------------------------------- stevnen over vannlinjestripen
def trace_stem_top():
    """Stevnens kant (vaar hvite baug mot den andre baatens hvite skrog), rad
    474-536. Kanten er svak; den finnes som sterkeste fall i lysstyrke langs
    raden naer en manuell linje (0,472)-(60,538)."""
    out = []
    for r in range(476, 536, 2):
        g = (r - 472) * 60.0 / 66.0
        u0 = int(max(g - 14, 1))
        u1 = int(g + 14)
        prof = smooth(Y[r, :], 3)
        d = np.diff(prof[u0:u1])
        k = int(np.argmax(np.abs(d)))
        if abs(d[k]) < 3:
            continue
        out.append((r, u0 + k + 0.5, d[k]))
    return np.array(out)


def trace_stem_front():
    """Stevnens kant gjennom stripen (rad 538-626): blaatt, lys stripe og
    moerk roed kant mot den andre baatens hvite skrog. Sterkeste endring i
    farge langs raden naer linja (57,533)-(140,605)-(168,624)."""
    gp = np.array([(533, 57.0), (605, 140.0), (624, 168.0)])
    out = []
    for r in range(538, 627, 1):
        g = float(np.interp(r, gp[:, 0], gp[:, 1]))
        u0 = int(max(g - 16, 1))
        u1 = int(g + 16)
        seg = A[r, u0:u1, :]
        k3 = np.ones(3) / 3
        seg = np.stack([np.convolve(np.pad(seg[:, i], 1, mode="edge"), k3, mode="valid") for i in range(3)], 1)
        d = np.linalg.norm(np.diff(seg, axis=0), axis=1)
        k = int(np.argmax(d))
        if d[k] < 6:
            continue
        # subpiksel: parabel gjennom toppen
        if 0 < k < len(d) - 1:
            a, b, cc = d[k - 1], d[k], d[k + 1]
            den = a - 2 * b + cc
            off = 0.5 * (a - cc) / den if abs(den) > 1e-9 else 0.0
        else:
            off = 0.0
        out.append((r, u0 + k + 0.5 + off, d[k]))
    return np.array(out)


# ---------------------------------------------------------------- vinduet
# Rammens ytre omriss, avlest paa forstoerret utsnitt (g_win, 3x): forreste
# punkt midt paa den runde forenden og bakerste punkt paa den skraa akterenden.
WINDOW = dict(fwd_end=(1322.0, 316.0), aft_end=(1641.0, 398.0),
              note="ytre kant av den lyse rammen; avlest for haand +-2 px")


if __name__ == "__main__":
    st = trace_strake()
    bt = trace_boottop()
    sh = trace_sheer(st)
    stem, bot = trace_forebody(bt)
    kle, kte, kbo = trace_keel()
    rte, rbo = trace_rudder()
    tr = trace_transom()
    sm = trace_stem_top()
    print("strake", len(st), "boottop", len(bt), "sheer", len(sh), "stem", len(stem), "bot", len(bot),
          "keel", len(kle), len(kte), len(kbo), "rudder", len(rte), len(rbo), "transom", len(tr), "stemtop", len(sm))
    cam = dict(
        image="docs/foto/IMG_9387.jpg", W=W_, H=H_,
        strake=st, strake_cols="u, oevre kant v, nedre kant v, senter v (moerkt baand, inkl. skygge under)",
        boottop=bt, boottop_cols="u, blaa overkant v, blaa underkant v (mot lys stripe), lysest rad i stripen, lys stripe -> roedt v",
        sheer=sh, sheer_cols="u, v for dekkskantens silhuett (hvit skrogside mot himmel/dekk), fargeavvik",
        keel_le=kle, keel_le_cols="v, u venstre kant av kjolen (roedt mot asfalt)",
        keel_te=kte, keel_te_cols="v, u hoeyre kant av kjolen",
        keel_bot=kbo, keel_bot_cols="u, v nederste roede rad under kjolen",
        rudder_te=rte, rudder_te_cols="v, u hoeyre (bakre) kant av roret",
        rudder_bot=rbo, rudder_bot_cols="u, v nederste roede rad paa roret",
        transom=tr, transom_cols="v, u hoeyre kant av skrogsiden ved akterspeilet (hvitt mot gult)",
        stem_top=sm, stem_top_cols="v, u stevnens kant over stripen (svak kant, hvitt mot hvitt), gradient",
        window=WINDOW,
    )
    c.save_json(cam, c.W + "/out/t9387_cam.json")
    print("lagret", c.W + "/out/t9387_cam.json", "(forkroppen: fk9387.py)")
