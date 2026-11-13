"""Smaa sporhjelpere for de nye akterbildene (n1_/n3_/n9526_-skriptene)."""
import numpy as np


def gi(guide, t):
    g = np.asarray(guide, float)
    return float(np.interp(t, g[:, 0], g[:, 1]))


def edge_sub(prof):
    """Sterkeste kant (subpiksel) i en profil: (indeks, gradient)."""
    g = np.gradient(np.asarray(prof, float))
    k = int(np.argmax(np.abs(g)))
    if 0 < k < len(g) - 1:
        a, b, cc = abs(g[k - 1]), abs(g[k]), abs(g[k + 1])
        den = a - 2 * b + cc
        return k + (0.5 * (a - cc) / den if abs(den) > 1e-9 else 0.0), float(g[k])
    return float(k), float(g[k])


def dark_center_col(Ls, u, vg, half=12, thr_frac=0.5, min_contrast=50):
    """Senter av et moerkt baand i kolonne u naer vg: (v, bredde) eller None."""
    lo, hi = int(vg - half), int(vg + half)
    prof = Ls[lo:hi, u]
    mn, bg = prof.min(), np.percentile(prof, 85)
    thr = mn + thr_frac * (bg - mn)
    k = int(np.argmin(prof))
    a = k
    while a > 0 and prof[a - 1] < thr:
        a -= 1
    b = k
    while b < len(prof) - 1 and prof[b + 1] < thr:
        b += 1
    if bg - mn < min_contrast or a == 0 or b == len(prof) - 1:
        return None
    return lo + 0.5 * (a + b), b - a + 1
