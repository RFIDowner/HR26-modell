"""Find long vertical lines (bulkheads, grid lines) in the profile and in the
plan, to check that both views share the same x axis."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from img import gray

a = gray()


def longest_runs(y0, y1, thr=170, minlen=60):
    sub = a[y0:y1, :] < thr
    W = sub.shape[1]
    best = np.zeros(W, int)
    where = np.zeros((W, 2), int)
    for x in range(W):
        col = sub[:, x]
        m = np.r_[False, col, False].astype(int)
        d = np.diff(m)
        st = np.where(d == 1)[0]
        en = np.where(d == -1)[0]
        if len(st):
            L = en - st
            i = int(np.argmax(L))
            best[x] = L[i]
            where[x] = (st[i] + y0, en[i] + y0)
    out = []
    x = 0
    while x < W:
        if best[x] >= minlen:
            j = x
            while j + 1 < W and best[j + 1] >= minlen * 0.5:
                j += 1
            seg = np.arange(x, j + 1)
            w = best[seg].astype(float)
            # centroid of the column darkness over the common run
            ys0, ys1 = where[seg[np.argmax(w)]]
            prof = a[ys0:ys1, max(x - 2, 0):j + 3].mean(axis=0)
            xs = np.arange(max(x - 2, 0), j + 3)
            ww = np.clip(200 - prof, 0, None)
            c = float(np.sum(xs * ww) / max(ww.sum(), 1e-9))
            out.append((round(c, 2), int(best[seg].max()), int(ys0), int(ys1)))
            x = j + 1
        else:
            x += 1
    return out


print("PROFILE (y 120-880):")
for r in longest_runs(120, 880):
    print("  x %.2f  len %d  y %d-%d" % r)
print("PLAN (y 1000-1665):")
for r in longest_runs(1000, 1665):
    print("  x %.2f  len %d  y %d-%d" % r)
