"""Robust dark-band tracker along columns. track(L, u_seed, v_seed, u_range, win, maxjump) -> rows [u, top, bot, ctr, min]"""
import numpy as np


def band_at(col, j0, win):
    lo = max(0, j0 - win); hi = min(len(col), j0 + win + 1)
    seg = col[lo:hi]
    j = lo + int(np.argmin(seg)); vmin = col[j]
    a = max(0, j - 10); b = min(len(col), j + 11)
    top_white = col[a:j].max() if j > a else col[j]
    bot_white = col[j + 1:b].max() if b > j + 1 else col[j]
    ref = min(top_white, bot_white)
    if ref - vmin < 40:
        return None
    half = vmin + 0.5 * (ref - vmin)
    k0 = j
    while k0 > 0 and col[k0] < half:
        k0 -= 1
    k1 = j
    while k1 < len(col) - 1 and col[k1] < half:
        k1 += 1
    t = k0 + (half - col[k0]) / (col[k0 + 1] - col[k0] + 1e-9)
    bb = k1 - 1 + (half - col[k1 - 1]) / (col[k1] - col[k1 - 1] + 1e-9)
    w = np.clip(half - col[k0:k1 + 1], 0, None)
    c = (np.arange(k0, k1 + 1) * w).sum() / max(w.sum(), 1e-9)
    return t, bb, c, vmin


def track(L, u_seed, v_seed, u_lo, u_hi, win=4, maxjump=1.5):
    out = {}
    for direction in (1, -1):
        v = v_seed
        u = u_seed
        while u_lo <= u <= u_hi:
            r = band_at(L[:, u], int(round(v)), win)
            if r is not None and abs(r[2] - v) <= maxjump + 0.5:
                out[u] = (u, r[0], r[1], r[2], r[3])
                v = r[2]
            u += direction
    return np.array([out[k] for k in sorted(out)])
