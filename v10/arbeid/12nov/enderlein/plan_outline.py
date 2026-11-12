"""Trace the deck outline (thick line) in the plan view, both sides, in
image pixels. The outline is the largest dark connected component in the
plan area; at each column the outermost run of that component is taken
and its intensity-weighted centre (and both edges) recorded. The ends
(bow tip, transom) are traced by rows.

Writes work/plan_outline_px.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from img import gray, WORK

a = gray()
Y0, Y1, X0, X1 = 960, 1720, 300, 2300
sub = a[Y0:Y1, X0:X1]
mask = sub < 150
mask = ndimage.binary_closing(mask, structure=np.ones((7, 7)))
lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
sizes = ndimage.sum(mask, lab, range(1, n + 1))
big = int(np.argmax(sizes)) + 1
comp = lab == big
ys, xs = np.nonzero(comp)
print("outline component px", int(sizes[big - 1]), "x", xs.min() + X0, xs.max() + X0,
      "y", ys.min() + Y0, ys.max() + Y0)


def run_centre(col, start, direction, thr=160):
    """From index `start` (first dark pixel seen from outside) walk inward
    while dark; return centroid, inner edge, outer edge (sub-pixel edges at
    half darkness)."""
    i = start
    idx = []
    while 0 <= i < len(col) and col[i] < thr:
        idx.append(i)
        i += direction
    # extend one px each side for edge interpolation
    idx = np.array(sorted(idx))
    w = np.clip(255.0 - col[idx], 0, None)
    c = float(np.sum(idx * w) / np.sum(w))
    # half-level edges
    lev = 0.5 * (255.0 + col[idx].min())
    lo, hi = idx[0], idx[-1]
    def edge(k_out, k_in):
        v0, v1 = col[k_out], col[k_in]
        if v0 == v1:
            return float(k_in)
        return k_out + (v0 - lev) / (v0 - v1) * (k_in - k_out)
    e_lo = edge(lo - 1, lo) if lo - 1 >= 0 else float(lo)
    e_hi = edge(hi + 1, hi) if hi + 1 < len(col) else float(hi)
    return c, e_lo, e_hi, float(col[idx].min()), len(idx)


def first_dark(col, start, direction, thr=160):
    # closing may start the component a few px outside the ink: walk inward to ink
    i = start
    for _ in range(8):
        if 0 <= i < len(col) and col[i] < thr:
            return i
        i += direction
    return start


top, bot = [], []
for xi in range(comp.shape[1]):
    yy = np.nonzero(comp[:, xi])[0]
    if len(yy) == 0:
        continue
    x = xi + X0
    col = sub[:, xi]
    c, elo, ehi, mn, wd = run_centre(col, first_dark(col, yy[0], +1), +1)
    top.append((x, c + Y0, elo + Y0, ehi + Y0, mn, wd))
    c, elo, ehi, mn, wd = run_centre(col, first_dark(col, yy[-1], -1), -1)
    bot.append((x, c + Y0, elo + Y0, ehi + Y0, mn, wd))

# ends by rows: bow = rightmost, transom = leftmost
bow, tr = [], []
for yi in range(comp.shape[0]):
    xx = np.nonzero(comp[yi, :])[0]
    if len(xx) == 0:
        continue
    y = yi + Y0
    row = sub[yi, :]
    c, elo, ehi, mn, wd = run_centre(row, first_dark(row, xx[-1], -1), -1)
    bow.append((c + X0, y, elo + X0, ehi + X0, mn, wd))
    c, elo, ehi, mn, wd = run_centre(row, first_dark(row, xx[0], +1), +1)
    tr.append((c + X0, y, elo + X0, ehi + X0, mn, wd))

json.dump(dict(top=top, bottom=bot, bow_rows=bow, transom_rows=tr,
               note="pixels; centre, edge_lo, edge_hi (along scan), min grey, run width"),
          open(os.path.join(WORK, "plan_outline_px.json"), "w"))
top = np.array(top)
bot = np.array(bot)
print("top side: min y centre", top[:, 1].min(), "at x", top[np.argmin(top[:, 1]), 0])
print("bottom side: max y centre", bot[:, 1].max(), "at x", bot[np.argmax(bot[:, 1]), 0])
bow = np.array(bow)
tr = np.array(tr)
print("bow tip: max x centre", bow[:, 0].max(), "at y", bow[np.argmax(bow[:, 0]), 1],
      " outer edge", bow[:, 3].max() if False else bow[np.argmax(bow[:, 0]), 2:4])
print("transom: min x centre", tr[:, 0].min(), "at y", tr[np.argmin(tr[:, 0]), 1],
      " edges", tr[np.argmin(tr[:, 0]), 2:4])
print("line width stats top", np.percentile(top[:, 5], [10, 50, 90]), "bottom", np.percentile(bot[:, 5], [10, 50, 90]))
