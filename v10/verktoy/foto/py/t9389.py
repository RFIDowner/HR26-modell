"""Sporing i IMG_9389 (3/4 forfra styrbord, lavt, paa land; 2000 x 1500).

Halvautomatisk: grove haandlinjer (GUESS) + kantsoek i fargene per kolonne
eller rad. Okkluderte omraader (stativets roer, puten, stroppen, stigen) er
tatt ut for haand. Lagrer
  ../out/t9389_cam.json       trekk til kameraet (ikke forkroppen)
  ../out/t9389_forkropp.json  forkroppens omriss under vann og stripens
                              nedre kant (lys -> roedt)
og et kontrollbilde (argv[1], valgfritt).

Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python t9389.py [kontroll.png]
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

import common as c

IMG = c.FOTO + "/IMG_9389.jpg"
A = np.asarray(Image.open(IMG).convert("RGB")).astype(float)
R_, G_, B_ = A[..., 0], A[..., 1], A[..., 2]
H_, W_ = G_.shape
RED = R_ - G_                       # roedhet (bunnstoff ~40-60, asfalt/himmel ~0)


def guess(pts, us):
    pts = np.asarray(pts, float)
    return np.interp(us, pts[:, 0], pts[:, 1])


def crossing(prof, v0, level, direction):
    """Foerste kryssing av level fra indeks v0 (direction +1 nedover)."""
    n = len(prof)
    i = v0
    while 0 <= i + direction < n:
        a, b = prof[i], prof[i + direction]
        if (a - level) * (b - level) <= 0 and a != b:
            return i + direction * (a - level) / (a - b)
        i += direction
    return np.nan


def col(ch, u, w=1):
    return ch[:, max(u - w, 0):u + w + 1].mean(1)


def row(ch, v, w=1):
    return ch[max(v - w, 0):v + w + 1, :].mean(0)


# ------------------------------------------------------------------ stripen
BT_GUESS = [(330, 492), (400, 457), (600, 405), (800, 377), (1000, 358), (1200, 330), (1500, 296), (1800, 240),
            (2000, 213)]
BT_SKIP = [(790, 870)]              # stativroeret krysser stripen


def trace_boottop():
    out = []
    for u in range(336, 1996, 4):
        if any(a <= u <= b for a, b in BT_SKIP):
            continue
        g = col(G_, u)
        vg = int(round(guess(BT_GUESS, u)))
        lo, hi = max(vg - 25, 0), min(vg + 25, H_ - 1)
        seg = g[lo:hi]
        # hvit -> blaa: stoerste fall
        d = seg[2:] - seg[:-2]
        i = int(np.argmin(d)) + 1
        white = np.median(g[max(lo - 15, 0):lo + i - 3]) if i > 4 else g[lo]
        blue_v = lo + i + 4
        blue = np.median(g[blue_v:blue_v + 6])
        vt = crossing(g, blue_v, 0.5 * (white + blue), -1)
        # den lyse stripen under den blaa: foerste lyse topp under blue_v
        j = blue_v
        while j < min(blue_v + 160, H_ - 2) and g[j] < 110:
            j += 1
        if j >= blue_v + 160:
            continue
        k = j
        while k < H_ - 1 and g[k] >= 100:
            k += 1
        ip = j + int(np.argmax(g[j:k + 1]))       # toppen av den lyse stripen
        cream = float(g[ip])
        maroon = float(np.median(g[k + 2:k + 10]))
        vc_top = crossing(g, ip, 0.5 * (cream + float(np.median(g[j - 8:j - 2]))), -1)
        vr = crossing(g, ip, 0.5 * (cream + maroon), +1)
        if (k - j) > 30 or not np.isfinite(vt) or not np.isfinite(vr) or not (0 < vr - vc_top < 20):
            continue
        out.append((u, vt, vc_top, vr, cream, maroon))
    return np.array(out)


# ------------------------------------------------------------------ fenderlisten
ST_GUESS = [(262, 335), (300, 268), (350, 232), (400, 203), (450, 175), (500, 148), (550, 120), (600, 95),
            (650, 70), (700, 45), (750, 18), (785, 0)]


def trace_strake():
    """Listen er et baand paa ca. 26-29 px: oevre del middels graa, nedre del
    moerk. Underkanten (moerk -> hvit) er skarp overalt; overkanten (hvit ->
    graa) bare der vinduets ramme ikke ligger inntil (u < 300 og u > 480)."""
    out = []
    for u in range(285, 776, 3):
        g = col(G_, u)
        vg = int(round(guess(ST_GUESS, u)))
        lo, hi = max(vg - 26, 0), min(vg + 26, H_ - 1)
        sm = np.convolve(g, np.ones(5) / 5.0, mode="same")
        i = lo + int(np.argmin(sm[lo:hi]))
        if i - lo < 2 or hi - i < 2:
            continue
        core = float(sm[i])
        below = float(np.median(g[i + 25:i + 40]))
        b = crossing(g, i, 0.5 * (core + below), +1)
        a = np.nan
        if u < 300 or u > 480:
            above = float(np.median(g[max(i - 50, 0):max(i - 32, 1)]))
            a = crossing(g, i, above - 45.0, -1)
            if np.isfinite(a) and (b - a < 15 or b - a > 40):
                a = np.nan
        if not np.isfinite(b) or b - i > 25:
            continue
        out.append((u, b, a))
    return np.array(out)


# ------------------------------------------------------------------ venstre silhuett (akterspeilets hjoerne)
def trace_left_sil():
    """Skrogets venstre omriss mot den gule baaten, rad 388-500: hvit -> gul."""
    out = []
    for v in range(388, 501, 3):
        b = row(B_, v)
        r = row(R_, v)
        u = 420
        while u > 240 and not (b[u] < 120 and r[u] > 140):
            u -= 1
        if u <= 240:
            continue
        hull = float(np.median(b[u + 15:u + 30]))
        bg = float(np.median(b[u - 10:u - 2]))
        x = crossing(b, u, 0.5 * (hull + bg), +1)
        out.append((v, x))
    return np.array(out)


# ------------------------------------------------------------------ kjolen og roret
def red_mask(th=22.0):
    return RED > th


def trace_keel():
    rm = RED
    le, te, bot = [], [], []
    for v in range(700, 896, 3):            # forkanten: hoeyre kant av det roede
        rr = row(rm, v)
        u = 830
        while u < 1100 and rr[u] > 20:
            u += 1
        if u >= 1100:
            continue
        hull = float(np.median(rr[u - 12:u - 4]))
        x = crossing(rr, u - 4, 0.5 * (hull + float(np.median(rr[u + 3:u + 10]))), +1)
        le.append((v, x))
    for v in range(672, 872, 3):            # bakkanten: venstre kant
        rr = row(rm, v)
        u = 760
        while u > 600 and rr[u] > 20:
            u -= 1
        if u <= 600:
            continue
        hull = float(np.median(rr[u + 4:u + 12]))
        x = crossing(rr, u + 4, 0.5 * (hull + float(np.median(rr[u - 10:u - 3]))), -1)
        te.append((v, x))
    for u in range(700, 935, 3):            # bunnen
        cc = col(rm, u)
        v = 830
        while v < 1000 and cc[v] > 20:
            v += 1
        if v >= 1000:
            continue
        hull = float(np.median(cc[v - 12:v - 4]))
        y = crossing(cc, v - 4, 0.5 * (hull + float(np.median(cc[v + 3:v + 10]))), +1)
        bot.append((u, y))
    return np.array(le), np.array(te), np.array(bot)


def trace_rudder():
    """Roret (roedt, u 470-545, v 600-735). Stroppen krysser diagonalt
    (u_s(v) = 473 + 0,84 (v - 630), ca. 8 px bred) og stigen staar bak:
    venstre kant soekes fra 12 px til venstre for stroppen."""
    rm = RED
    left, right, bot = [], [], []
    us = lambda v: 473.0 + 0.84 * (v - 630.0)
    for v in range(622, 682, 2):              # hoeyre kant (forkanten)
        rr = row(rm, v)
        u = 528
        while u < 565 and rr[u] > 25:
            u += 1
        if u < 565:
            hull = float(np.median(rr[u - 8:u - 3]))
            right.append((v, crossing(rr, u - 3, 0.5 * (hull + float(np.median(rr[u + 2:u + 7]))), +1)))
    for v in range(646, 722, 2):              # venstre kant (bakkanten)
        rr = row(rm, v)
        u = int(us(v) - 12)
        while u > 455 and rr[u] > 25:
            u -= 1
        if u > 455:
            hull = float(np.median(rr[u + 3:u + 8]))
            left.append((v, crossing(rr, u + 3, 0.5 * (hull + float(np.median(rr[u - 7:u - 2]))), -1)))
    for u in range(484, 523, 2):              # bunnen
        cc = col(rm, u)
        v = 700
        while v < 760 and cc[v] > 25:
            v += 1
        if v < 760:
            hull = float(np.median(cc[v - 8:v - 3]))
            bot.append((u, crossing(cc, v - 3, 0.5 * (hull + float(np.median(cc[v + 2:v + 7]))), +1)))
    return np.array(left), np.array(right), np.array(bot)


# ------------------------------------------------------------------ bunnens omriss
BOT_GUESS = [(340, 520), (500, 610), (650, 655), (1000, 680), (1100, 664), (1200, 655), (1300, 644), (1400, 630),
             (1500, 609), (1600, 584), (1700, 546), (1800, 500), (1900, 432), (1960, 375), (1998, 318)]
# stativroeret (u 1040-1102), puten (1158-1264, med skyggen), det loddrette roeret (1304-1354)
BOT_SKIP = [(1040, 1102), (1158, 1264), (1304, 1354)]


def trace_bottom(u0, u1, skip, step=3):
    out = []
    for u in range(u0, u1 + 1, step):
        if any(a <= u <= b for a, b in skip):
            continue
        cc = col(RED, u)
        gg = col(G_, u)
        vg = int(round(guess(BOT_GUESS, u)))
        v = vg - 45
        # gaa ned gjennom det roede til roedheten faller under 12 tre piksler paa rad
        while v < vg + 45 and not (cc[v] < 12 and cc[v + 1] < 12 and cc[v + 2] < 12):
            v += 1
        if v >= vg + 45:
            continue
        hull = float(np.median(cc[v - 10:v - 3]))
        bg = float(np.median(cc[v + 1:v + 6]))
        y = crossing(cc, v - 3, 0.5 * (hull + bg), +1)
        # kontroll med lysheten: bakgrunnen er lysere enn den skyggede bunnen
        gy = crossing(gg, v - 3, 0.5 * (float(np.median(gg[v - 10:v - 3])) + float(np.median(gg[v + 2:v + 7]))), +1)
        out.append((u, y, gy, hull, bg))
    return np.array(out)


def trace_front(v0=352, v1=440):
    """Forfotens bratte omriss helt til hoeyre (u > 1885): per rad, skrog
    (moerkt, G < 100) -> bakgrunn (himmel/hvit baat, G > 130)."""
    out = []
    for v in range(v0, v1 + 1, 2):
        g = row(G_, v)
        u = 1850
        while u < W_ - 3 and g[u] < 130:
            u += 1
        if u >= W_ - 3:
            continue
        hull = float(np.median(g[u - 12:u - 4]))
        bg = float(np.median(g[u + 2:min(u + 9, W_)]))
        out.append((v, crossing(g, u - 4, 0.5 * (hull + bg), +1)))
    return np.array(out)


def window_fwd_end():
    """Vinduets forende: den ytre rammens hoeyre ytterpunkt, lest av for haand
    i 8x forstoerrelse (u 483,5, v 75-90)."""
    return (483.5, 82.0)


def smooth_filter(u, v, half=24.0, tol=2.5):
    """Fjerner punkter som avviker mer enn tol px fra en lokal lineaer
    tilpasning (robust, naboer innen +-half px i u)."""
    ok = np.isfinite(v)
    keep = np.zeros(len(u), bool)
    for i in range(len(u)):
        if not ok[i]:
            continue
        m = ok & (np.abs(u - u[i]) <= half)
        m[i] = False
        if m.sum() < 4:
            continue
        uu, vv = u[m], v[m]
        p = np.polyfit(uu - u[i], vv, 1)
        r = vv - np.polyval(p, uu - u[i])
        good = np.abs(r - np.median(r)) < 3.0 * max(1.48 * np.median(np.abs(r - np.median(r))), 0.7)
        if good.sum() >= 3:
            p = np.polyfit(uu[good] - u[i], vv[good], 1)
        keep[i] = abs(v[i] - p[1]) < tol
    return keep


if __name__ == "__main__":
    bt = trace_boottop()
    for k in (1, 2, 3):
        bad = ~smooth_filter(bt[:, 0], bt[:, k])
        bt[bad, k] = np.nan
    st = trace_strake()
    ls = trace_left_sil()
    kle, kte, kbo = trace_keel()
    rl, rr, rb = trace_rudder()
    fb = trace_bottom(1095, 1996, BOT_SKIP)
    ab = trace_bottom(345, 650, [(455, 545)])          # akterkroppen (bare kontroll)
    wf = window_fwd_end()
    print("stripe", len(bt), "liste", len(st), "venstre", len(ls), "kjol", len(kle), len(kte), len(kbo),
          "ror", len(rl), len(rr), len(rb), "bunn", len(fb), "akter", len(ab), "vindu", wf)
    fr = trace_front()
    cam = dict(
        note="IMG_9389 2000x1500, piksler (u mot hoeyre, v nedover). Se t9389.py.",
        boottop=bt, boottop_cols="u, v_blaa_overkant, v_lys_stripe_overkant, v_roedt_start (lys->roedt), G_lys, G_roedt",
        strake=st, strake_cols="u, v_underkant (moerk -> hvit), v_overkant (hvit -> graa, nan ved vinduet)",
        left_sil=ls, left_sil_cols="v, u: skrogets venstre omriss (hvit/blaa mot gul baat), akterspeilets hjoerne",
        keel_le=kle, keel_te=kte, keel_bot=kbo, keel_cols="le/te: v, u (hoeyre/venstre kant); bot: u, v",
        rudder_left=rl, rudder_right=rr, rudder_bot=rb, window_fwd=wf,
        aft_bottom=ab, aft_bottom_cols="u, v (roedhet), v (lyshet), roedhet skrog, roedhet bakgrunn")
    c.save_json(cam, c.W + "/out/t9389_cam.json")
    keep = (fb[:, 0] <= 1890) & smooth_filter(fb[:, 0], fb[:, 1], half=20.0, tol=2.5)
    print("bunn: %d av %d kolonner beholdt" % (keep.sum(), (fb[:, 0] <= 1890).sum()))
    fk = dict(
        photo="docs/foto/IMG_9389.jpg", W=W_, H=H_,
        note=("Forkroppen under vann i IMG_9389 (3/4 forfra styrbord, kamera ca. 1,6 m over bakken, litt over "
              "DWL, ser ned ca. 10 grader). Piksler: u mot hoeyre, v nedover. Sporet med t9389.py (kantsoek i "
              "fargene, terskel midt mellom skrog og bakgrunn)."),
        bottom=fb[keep][:, [0, 1]],
        bottom_desc=("[u, v] per bildekolonne u 1095-1890 (hvert 3. px, glatthetsfilter 2,5 px): nederste kant av det roede skroget mot "
                     "bakgrunnen (asfalt, stativ i bakgrunnen, fjerne baater), sub-px kryssing av roedhet R-G. "
                     "Utelatt: u 1040-1102 (stativroeret som krysser omrisset ved kjolens forkant/hulkil), "
                     "1158-1264 (puten under skroget og skyggen ved den), 1304-1354 (stativets loddrette roer). Omrisset dannes her "
                     "av bunnen naer senterlinjen/kimingen paa styrbord side sett litt ovenfra."),
        bottom_vG=fb[keep][:, [0, 2]],
        bottom_vG_desc="[u, v] samme kant fra lysheten G (kontroll; avviker typisk < 2 px)",
        front=fr,
        front_desc=("[v, u] per bilderad v 352-440: forfotens bratte omriss helt til hoeyre (skrog -> himmel/hvit "
                    "baat), sub-px kryssing av G. Over v ~ 345 gaar omrisset ut av bildet (u > 2000)."),
        bt_red=bt[np.isfinite(bt[:, 3])][:, [0, 3]],
        bt_red_desc=("[u, v] per kolonne u 336-1996 (hvert 4. px; 790-870 utelatt for stativroeret): "
                     "vannlinjestripens nedre kant = underkanten av den lyse (kremhvite) linja under den blaa, "
                     "der det moerke roede begynner. Paa skroget er dette en linje z ~ +38 mm etter IMG_9370, men "
                     "med kameraet fra cam9389.py ligger den ca. 135 mm hoeyere (se cam9389.json)."),
        bt_top=bt[np.isfinite(bt[:, 1])][:, [0, 1]],
        bt_top_desc="[u, v] blaa overkant (hvit -> blaa), samme kolonner",
        aft_bottom=ab[:, [0, 1]],
        aft_bottom_desc="[u, v] akterkroppens nedre kant u 345-650 (stoeyete, bare kontroll; ikke i resid)")
    c.save_json(fk, c.W + "/out/t9389_forkropp.json")
    if len(sys.argv) > 1:
        im = Image.open(IMG).convert("RGB")
        d = ImageDraw.Draw(im)

        def dots(P, col_, r=2):
            for a, b in P:
                if np.isfinite(a) and np.isfinite(b):
                    d.ellipse([a - r, b - r, a + r, b + r], fill=col_)
        dots(bt[:, [0, 1]], (255, 255, 0)); dots(bt[:, [0, 2]], (0, 255, 255)); dots(bt[:, [0, 3]], (0, 255, 0))
        dots(st[:, [0, 1]], (255, 0, 255)); dots(st[:, [0, 2]], (255, 128, 255))
        dots(ls[:, [1, 0]], (255, 0, 0))
        dots(kle[:, [1, 0]], (0, 255, 0)); dots(kte[:, [1, 0]], (0, 255, 0)); dots(kbo, (0, 255, 0))
        dots(rl[:, [1, 0]], (255, 255, 0)); dots(rr[:, [1, 0]], (255, 255, 0)); dots(rb, (255, 255, 0))
        dots(fb[:, [0, 1]], (255, 255, 255)); dots(fb[:, [0, 2]], (0, 0, 255), 1)
        dots(ab[:, [0, 1]], (255, 128, 0)); dots(fr[:, [1, 0]], (255, 0, 0))
        if wf:
            dots([wf], (255, 0, 0), 5)
        im.save(sys.argv[1])
