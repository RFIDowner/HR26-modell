"""Guided line tracer for the scanned drawing.

A guide polyline (read off zoomed crops, +-3 px) is resampled every `step`
px. At each sample the grey profile along the normal is read (bilinear,
0.25 px), the dark runs are found and the one chosen (nearest the guide, or
the outermost on a given side) gives a sub-pixel centre: the intensity-
weighted centroid of the run. Outliers (jumps against the neighbours) are
dropped.
"""
import numpy as np
from scipy.ndimage import map_coordinates


def resample(poly, step):
    p = np.asarray(poly, float)
    seg = np.hypot(*np.diff(p, axis=0).T)
    s = np.r_[0.0, np.cumsum(seg)]
    n = max(int(s[-1] / step), 1)
    ss = np.linspace(0.0, s[-1], n + 1)
    x = np.interp(ss, s, p[:, 0])
    y = np.interp(ss, s, p[:, 1])
    # tangents
    t = np.gradient(np.c_[x, y], axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1)[:, None], 1e-9)
    nrm = np.c_[-t[:, 1], t[:, 0]]          # left normal in image coords (x right, y down)
    return np.c_[x, y], nrm


def snap(a, poly, step=2.0, search=4.0, thr=170.0, pick="nearest", side=None,
         min_dark=None, max_jump=1.5, smooth_w=0):
    """Return array of (x, y, minval, offset) on the drawn line.

    pick: 'nearest' - run closest to the guide;
          'outer'   - run furthest toward `side` (+1 = along +normal,
                      -1 = along -normal) among runs within the window;
          'darkest' - darkest run.
    """
    pts, nrm = resample(poly, step)
    ts = np.arange(-search, search + 1e-9, 0.25)
    out = []
    for p, n in zip(pts, nrm):
        xs = p[0] + ts * n[0]
        ys = p[1] + ts * n[1]
        prof = map_coordinates(a, [ys, xs], order=1, mode="nearest")
        dk = prof < thr
        if not dk.any():
            out.append((np.nan, np.nan, np.nan, np.nan))
            continue
        m = np.r_[False, dk, False].astype(int)
        d = np.diff(m)
        st = np.where(d == 1)[0]
        en = np.where(d == -1)[0] - 1
        runs = []
        for s, e in zip(st, en):
            w = np.clip(thr - prof[s:e + 1], 0, None) + 1e-6
            c = float(np.sum(ts[s:e + 1] * w) / np.sum(w))
            runs.append((c, float(prof[s:e + 1].min())))
        if min_dark is not None:
            runs = [r for r in runs if r[1] <= min_dark] or runs
        if pick == "nearest":
            c, mv = min(runs, key=lambda r: abs(r[0]))
        elif pick == "outer":
            c, mv = max(runs, key=lambda r: side * r[0])
        else:
            c, mv = min(runs, key=lambda r: r[1])
        out.append((p[0] + c * n[0], p[1] + c * n[1], mv, c))
    out = np.array(out, float)
    ok = ~np.isnan(out[:, 0])
    # reject jumps: offset differs from the running median of neighbours
    off = out[:, 3].copy()
    for i in range(len(out)):
        if not ok[i]:
            continue
        lo, hi = max(0, i - 4), min(len(out), i + 5)
        nb = off[lo:hi][ok[lo:hi]]
        if len(nb) >= 3 and abs(off[i] - np.median(nb)) > max_jump:
            ok[i] = False
    return out[ok]


def column_scan(a, x0, x1, y_guide, search=5, thr=170, pick="nearest", step=1):
    """For near-horizontal lines: for each column x in [x0, x1] take the dark
    run nearest y_guide(x) (callable) within +-search; centroid in y."""
    res = []
    for x in range(int(x0), int(x1) + 1, step):
        yg = y_guide(x)
        ylo, yhi = int(np.floor(yg - search)), int(np.ceil(yg + search))
        prof = a[ylo:yhi + 1, x]
        dk = prof < thr
        if not dk.any():
            continue
        m = np.r_[False, dk, False].astype(int)
        d = np.diff(m)
        st = np.where(d == 1)[0]
        en = np.where(d == -1)[0] - 1
        runs = []
        for s, e in zip(st, en):
            w = np.clip(thr - prof[s:e + 1], 0, None) + 1e-6
            c = ylo + float(np.sum(np.arange(s, e + 1) * w) / np.sum(w))
            runs.append((c, float(prof[s:e + 1].min()), e - s + 1))
        if pick == "nearest":
            r = min(runs, key=lambda r: abs(r[0] - yg))
        elif pick == "top":
            r = min(runs, key=lambda r: r[0])
        elif pick == "bottom":
            r = max(runs, key=lambda r: r[0])
        else:
            r = min(runs, key=lambda r: r[1])
        res.append((x, r[0], r[1], r[2]))
    return np.array(res, float)


def row_scan(a, y0, y1, x_guide, search=5, thr=170, pick="nearest", step=1):
    """For near-vertical lines: for each row y take the run nearest x_guide(y)."""
    res = []
    for y in range(int(y0), int(y1) + 1, step):
        xg = x_guide(y)
        xlo, xhi = int(np.floor(xg - search)), int(np.ceil(xg + search))
        prof = a[y, xlo:xhi + 1]
        dk = prof < thr
        if not dk.any():
            continue
        m = np.r_[False, dk, False].astype(int)
        d = np.diff(m)
        st = np.where(d == 1)[0]
        en = np.where(d == -1)[0] - 1
        runs = []
        for s, e in zip(st, en):
            w = np.clip(thr - prof[s:e + 1], 0, None) + 1e-6
            c = xlo + float(np.sum(np.arange(s, e + 1) * w) / np.sum(w))
            runs.append((c, float(prof[s:e + 1].min()), e - s + 1))
        if pick == "nearest":
            r = min(runs, key=lambda r: abs(r[0] - xg))
        elif pick == "left":
            r = min(runs, key=lambda r: r[0])
        elif pick == "right":
            r = max(runs, key=lambda r: r[0])
        else:
            r = min(runs, key=lambda r: r[1])
        res.append((r[0], y, r[1], r[2]))
    return np.array(res, float)
