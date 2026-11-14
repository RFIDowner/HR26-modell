"""Sporing i IMG_9395 (baaten henger i travelliften, sett forfra-nedenfra paa babord baug).

Alle koordinater er piksler i docs/foto/IMG_9395_mage.jpg (2400 x 1800; foer 14.11 IMG_9395.jpg), u mot hoeyre, v nedover.
Skriver out/t9395_raw.json: alle spor (fenderlist, stripe, silhuetter, kjol, ror, roedt/graatt-grensen).
forkropp9395.py lager out/t9395_forkropp.json (forkroppen, med beskrivelse) av dette og kameraet.

Kjoeres fra denne mappa: python ../../../../tools/memcap.py --gb 3 -- python t9395.py
"""
import json

import numpy as np
from PIL import Image

import common as c

IMG = c.FOTO + "/IMG_9395_mage.jpg"
A = np.asarray(Image.open(IMG).convert("RGB")).astype(float)
H, W = A.shape[:2]
R_, G_, B_ = A[..., 0], A[..., 1], A[..., 2]
LUM = A.mean(2)
# himmel: blaa (b >> r) eller lys skye (alle kanaler hoeye og lite metning)
SKY = ((B_ - R_ > 35) & (B_ > 140)) | ((np.minimum(np.minimum(R_, G_), B_) > 165) & (B_ - R_ > 5))
RED = (R_ - G_ > 10) & (R_ - B_ > -2) & (LUM < 130)


def runs(m):
    """Start/slutt (inkl.) for sammenhengende True-omraader i 1-D boolsk m."""
    d = np.diff(np.r_[0, m.astype(int), 0])
    s = np.nonzero(d == 1)[0]
    e = np.nonzero(d == -1)[0] - 1
    return list(zip(s, e))


def sub_edge(prof, i0, i1):
    """Subpikselkant mellom indeks i0 (side A) og i1 (side B): der profilen krysser
    midtverdien mellom snittet 2 px inne paa hver side."""
    n = len(prof)
    step = 1 if i1 > i0 else -1
    ia = np.clip(i0 - step * np.arange(0, 3), 0, n - 1)
    ib = np.clip(i1 + step * np.arange(0, 3), 0, n - 1)
    a, b = prof[ia].mean(), prof[ib].mean()
    mid = 0.5 * (a + b)
    lo, hi = min(i0, i1) - 2, max(i0, i1) + 2
    lo, hi = max(lo, 0), min(hi, n - 1)
    seg = prof[lo:hi + 1]
    idx = np.arange(lo, hi + 1)
    # foerste kryssing fra A-siden
    order = idx if step > 0 else idx[::-1]
    sv = prof[order]
    sgn = np.sign(sv - mid)
    k = np.nonzero(sgn[1:] != sgn[:-1])[0]
    if len(k) == 0 or abs(b - a) < 15:
        return 0.5 * (i0 + i1)
    j = k[0]
    p0, p1 = sv[j], sv[j + 1]
    t = (mid - p0) / (p1 - p0) if p1 != p0 else 0.5
    return float(order[j] + step * t)


def poly(pts, xs):
    pts = np.asarray(pts, float)
    return np.interp(xs, pts[:, 0], pts[:, 1])


# ------------------------------------------------------------- fenderlisten
STRAKE_GUIDE = [(880, 330), (1000, 372), (1300, 520), (1450, 600), (1600, 690), (1700, 775), (1745, 835)]


def trace_strake():
    out = []
    for u in range(885, 1742):
        v0 = int(poly(STRAKE_GUIDE, u))
        ys = np.arange(max(v0 - 45, 0), min(v0 + 45, H))
        L = LUM[ys, u]; bl = (B_ - R_)[ys, u]
        blk = (L < 50) & (bl < 30)
        rr = [r for r in runs(blk) if r[1] - r[0] >= 4]
        if not rr:
            continue
        # svart baand: det lengste nær ledelinjen
        r = max(rr, key=lambda r: (r[1] - r[0]) - 0.3 * abs(0.5 * (ys[r[0]] + ys[r[1]]) - v0))
        bt, bb = ys[r[0]], ys[r[1]]
        if bb - bt > 30:
            continue
        # under baandet skal det vaere lys topside
        below = LUM[bb + 3:bb + 9, u]
        if len(below) == 0 or below.mean() < 120:
            continue
        prof = LUM[:, u]
        e_bot = sub_edge(prof, bb, bb + 1)
        # blaatt rett over det svarte
        bu = (B_ - R_)[:, u]
        k = bt - 1
        while k > bt - 30 and (bu[k] > 35 or LUM[k, u] < 60):
            k -= 1
        blue_top = None
        if bt - k >= 5 and LUM[k - 2:k + 1, u].mean() > 150:
            blue_top = sub_edge(prof, k + 1, k)
        out.append((u, float(bt), e_bot, blue_top if blue_top is not None else np.nan))
    return np.array(out, float)


# --------------------------------------------------------- vannlinjestripen
STRIPE_GUIDE = [(1020, 705), (1100, 728), (1300, 790), (1500, 850), (1600, 872), (1700, 912), (1725, 945)]


def trace_stripe():
    out = []
    for u in range(1020, 1726):
        v0 = int(poly(STRIPE_GUIDE, u))
        ys = np.arange(v0 - 40, v0 + 45)
        bu = (B_ - R_)[ys, u]; L = LUM[ys, u]
        blue = (bu > 25) & (L < 130)
        rr = [r for r in runs(blue) if r[1] - r[0] >= 5]
        if not rr:
            continue
        r = max(rr, key=lambda r: r[1] - r[0])
        t, b = ys[r[0]], ys[r[1]]
        # over: hvit topside; under: kremlinje (lys) og saa roedt
        if LUM[t - 6:t - 2, u].mean() < 120:
            continue
        k = b + 1
        while k < b + 14 and not RED[k, u]:
            k += 1
        if k >= b + 14 or k - b < 2:
            continue
        cream = LUM[b + 1:k, u]
        if cream.max() < 100:
            continue
        prof = LUM[:, u]
        e_top = sub_edge(prof, t - 1, t)
        e_bc = sub_edge(prof, b, b + 1)
        # kremlinje -> roedt: bruk lum
        kc = b + 1 + int(np.argmax(cream))
        e_red = sub_edge(prof, k - 1, k)
        out.append((u, e_top, e_bc, e_red))
    return np.array(out, float)


# ----------------------------------------------------- silhuetter mot himmel
def scan_edge(cols, rows, T=40.0, minrun=10, nref=10):
    """Langs en skannelinje (pikselkoordinater cols, rows; foerst himmel): foerste kant
    der fargen avviker mer enn T fra medianen av de nref foregaaende pikslene i minst
    minrun piksler paa rad. Returnerer subpikselposisjon som brøkindeks, eller None."""
    cols = np.asarray(cols); rows = np.asarray(rows)
    ok = (cols >= 0) & (cols < W) & (rows >= 0) & (rows < H)
    cols, rows = cols[ok], rows[ok]
    Cc = A[rows, cols]
    n = len(Cc)
    for i in range(nref + 2, n - minrun - 6):
        ref = np.median(Cc[i - nref - 2:i - 2], axis=0)
        d = np.linalg.norm(Cc[i:i + minrun] - ref, axis=1)
        if (d > T).all():
            ins = Cc[i + 3:i + 9].mean(0)
            dd = ins - ref
            den = float(dd @ dd)
            if den < 1e-6:
                return float(i)
            t = (Cc[i - 3:i + 4] - ref) @ dd / den          # 0 = himmel, 1 = skrog
            k = np.nonzero(t >= 0.5)[0]
            if len(k) == 0:
                return float(i)
            j = k[0]
            if j == 0:
                return float(i - 3)
            t0, t1 = t[j - 1], t[j]
            return float(i - 3 + j - 1 + (0.5 - t0) / max(t1 - t0, 1e-6))
    return None


def trace_left(rows, u_start, u_len=400, **kw):
    """Venstre silhuett per rad: skann mot hoeyre fra u_start(v)."""
    out = []
    for v in rows:
        u0 = int(u_start(v))
        us = np.arange(u0, u0 + u_len)
        e = scan_edge(us, np.full(len(us), v), **kw)
        if e is not None:
            out.append((v, u0 + e))
    return np.array(out, float)


def trace_bottom(cols, v_start, v_len=300, **kw):
    """Nedre silhuett per kolonne: skann oppover fra v_start(u)."""
    out = []
    for u in cols:
        v0 = int(v_start(u))
        vs = np.arange(v0, v0 - v_len, -1)
        e = scan_edge(np.full(len(vs), u), vs, **kw)
        if e is not None:
            out.append((u, v0 - e))
    return np.array(out, float)


def trace_right(rows, u_start, u_len=300, **kw):
    """Hoeyre silhuett per rad: skann mot venstre fra u_start(v)."""
    out = []
    for v in rows:
        u0 = int(u_start(v))
        us = np.arange(u0, u0 - u_len, -1)
        e = scan_edge(us, np.full(len(us), v), **kw)
        if e is not None:
            out.append((v, u0 - e))
    return np.array(out, float)


# ----------------------------------------------- roedt / graatt paa forfoten
def trace_red_inner(cols, v_lo):
    """Nedre grense for det roede (babord bunn) i kolonner paa forfoten: skann oppover
    fra silhuetten til foerste roede run."""
    out = []
    for u in cols:
        v = int(v_lo(u))
        k = v
        while k > v - 200 and not (RED[k, u] and RED[k - 1, u] and RED[k - 2, u] and RED[k - 3, u]):
            k -= 1
        if k <= v - 200:
            continue
        prof = (R_ - B_)[:, u]
        out.append((u, sub_edge(prof, k, k + 1)))
    return np.array(out, float)


def trace_red_inner_rows(rows, u_lo):
    out = []
    for v in rows:
        u = int(u_lo(v))
        k = u
        while k < u + 200 and not (RED[v, k] and RED[v, k + 1] and RED[v, k + 2] and RED[v, k + 3]):
            k += 1
        if k >= u + 200:
            continue
        prof = (R_ - B_)[v, :]
        out.append((v, sub_edge(prof, k - 1, k)))
    return np.array(out, float)


def red_bottom_cols(cols, v0, v1):
    out = []
    for u in cols:
        m = RED[v0:v1, u]
        rr = [r for r in runs(m) if r[1] - r[0] >= 7]
        if not rr:
            continue
        k = v0 + rr[-1][1]
        out.append((u, sub_edge((R_ - G_)[:, u], k, k + 1)))
    return np.array(out, float)


def clean(a, win=15, tol=3.0, it=3):
    """Fjern punkter som avviker mer enn tol px fra loepende median (win punkter)."""
    a = np.asarray(a, float)
    for _ in range(it):
        if len(a) < win:
            return a
        m = np.array([np.median(a[max(i - win // 2, 0):i + win // 2 + 1, 1]) for i in range(len(a))])
        k = np.abs(a[:, 1] - m) <= tol
        if k.all():
            break
        a = a[k]
    return a


LEFT_GUIDE = [(345, 862), (500, 920), (700, 1000), (850, 1060), (950, 1130)]

if __name__ == "__main__":
    st = trace_strake()
    sp = trace_stripe()
    # venstre silhuett (stevn og forfot): skann fra himmelen mot hoeyre
    left = trace_left(range(348, 946), u_start=lambda v: poly(LEFT_GUIDE, v) - 70)
    # bunnen av forkroppen: skann oppover fra himmelen (tauet i u 1218-1250 hoppes over)
    cols = [u for u in range(1100, 1336) if not (1216 <= u <= 1252)]
    BOT_GUIDE = [(1100, 912), (1130, 955), (1160, 982), (1200, 1008), (1250, 1033), (1335, 1059)]
    bot = trace_bottom(cols, v_start=lambda u: poly(BOT_GUIDE, u) + 22, v_len=60)
    # kjolen: forkant mot himmel, bakkant og bunn etter roedfarge
    keel_left = trace_left(range(1062, 1222), u_start=lambda v: 1262)
    keel_right = trace_right(range(1203, 1250), u_start=lambda v: 1565, u_len=120)
    keel_bot = red_bottom_cols(range(1418, 1522), 1150, 1300)
    rud_left = trace_left(range(1085, 1212), u_start=lambda v: 1556, u_len=120)
    rud_right = trace_right(range(1085, 1218), u_start=lambda v: 1690, u_len=120)
    rud_bot = trace_bottom(range(1606, 1652), v_start=lambda u: 1226, v_len=60, minrun=6)
    aft_right = trace_right(range(842, 1070), u_start=lambda v: 1790)
    red_c = trace_red_inner([int(u) for u in bot[:, 0] if u >= 1130],
                            v_lo=lambda u: np.interp(u, bot[:, 0], bot[:, 1]) - 3)
    red_r = trace_red_inner_rows(range(700, 1000), u_lo=lambda v: np.interp(v, left[:, 0], left[:, 1]) + 3)
    left, bot, keel_left, keel_right, keel_bot, rud_left, rud_right, rud_bot, aft_right, red_c, red_r = [
        clean(a) for a in (left, bot, keel_left, keel_right, keel_bot, rud_left, rud_right, rud_bot, aft_right, red_c, red_r)]
    res = dict(strake=st, stripe=sp, left=left, bottom=bot, keel_left=keel_left, keel_right=keel_right,
               keel_bot=keel_bot, rud_left=rud_left, rud_right=rud_right, rud_bot=rud_bot,
               aft_right=aft_right, red_inner_cols=red_c, red_inner_rows=red_r)
    for k, v in res.items():
        print(k, np.shape(v))
    c.save_json(res, c.W + "/out/t9395_raw.json")
