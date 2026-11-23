"""Trace IMG_9388 (bow head-on, on land), full-size upright photo 1500 x 2000.

Outputs ../traces/t9388.json with
  rail_left / rail_right : [v, u] outer edge of the dark rub-rail band (from the
                           earlier m9388.json trace, rows 0..630, re-checked here)
  stem                   : [v, u] centre of the stem highlight (m9388.json)
  keel_left / keel_right : [v, u] keel-fin edges (redness crossing), rows clear of the stand
  keel_bottom_v          : lowest red row of the fin
  uw_left / uw_right     : [v, u] outline of the red antifouling region (underwater body)
  bt_stem_v              : boot-top top edge where it crosses the stem
"""
import sys, json
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/undervann/py")
import numpy as np
from scipy import ndimage as ndi
import uw

a = uw.photo("IMG_9388").astype(float)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
red = R - np.maximum(G, B)
reds = ndi.uniform_filter1d(red, 3, axis=1)
m = json.load(open(uw.SNAP + "/photo/m9388.json"))
out = {}

# rail band outer edges (rows 0..630)
L = np.array(m["left"], float); Rr = np.array(m["right"], float)
out["rail_left"] = [[v, ob] for v, ob, ib in L if v <= 630]
out["rail_right"] = [[v, ob] for v, ob, ib in Rr if v <= 630]
st = np.array(m["stem"], float)
# stem: the shaded stripe of the rounded stem; centre = mid-point of the two
# half-level crossings (left side level, stripe minimum, right side level)
Lum0 = ndi.uniform_filter(a.mean(2), 3)
stem = []
for v in range(10, 500, 4):
    prof = Lum0[v]
    l1, l2 = np.median(prof[575:605]), np.median(prof[700:730])
    i0 = 615 + int(np.argmin(prof[615:685]))
    lm = prof[i0]
    hl, hr = 0.5 * (l1 + lm), 0.5 * (l2 + lm)
    i = i0
    while i > 580 and prof[i - 1] < hl:
        i -= 1
    el = i - (hl - prof[i]) / (prof[i - 1] - prof[i] + 1e-9)
    j = i0
    while j < 720 and prof[j + 1] < hr:
        j += 1
    er = j + (hr - prof[j]) / (prof[j + 1] - prof[j] + 1e-9)
    stem.append([v, 0.5 * (el + er), el, er])
out["stem"] = stem


def crossing(prof, u0, thr, direction):
    """first sub-pixel crossing of prof above thr scanning from u0 in direction (+1/-1)."""
    n = len(prof)
    i = u0
    while 0 < i < n - 1:
        j = i + direction
        if prof[i] < thr <= prof[j]:
            return i + direction * (thr - prof[i]) / (prof[j] - prof[i])
        i = j
    return np.nan


# keel fin: left edge in shade (threshold 12), right edge lit (threshold 50)
kl, kr = [], []
for v in list(range(1090, 1196, 2)) + list(range(1232, 1306, 2)):
    prof = reds[v]
    ul = crossing(prof, 600, 12.0, +1)
    ur = crossing(prof, 730, 50.0, -1)
    if np.isfinite(ul) and 610 < ul < 660:
        kl.append([v, ul])
    if np.isfinite(ur) and 670 < ur < 715:
        kr.append([v, ur])
out["keel_left"], out["keel_right"] = kl, kr
col = reds[:, 640:700].max(1)
rows = np.nonzero(col[1250:1400] > 25)[0]
out["keel_bottom_v"] = float(1250 + rows.max()) if len(rows) else None

# underwater outline: red chromaticity r = R/(R+G+B) > 0.45 (lit and shaded
# antifouling).  Per row the outermost red pixel that starts a run of >= 4 red
# pixels, inside a region of interest that keeps the neighbouring boats out.
# The stand pipes lie inside the outline here (red shows outside them), so they
# do not move the edge.  flag = 1 where the pixels just outside are dark.
s_ = a.sum(2) + 1.0
chrom = a[..., 0] / s_
redm = (chrom > 0.45) & (s_ > 60)
run = ndi.uniform_filter1d(redm.astype(float), 4, axis=1, origin=-1) > 0.99   # run starting here (rightwards)
runl = ndi.uniform_filter1d(redm.astype(float), 4, axis=1, origin=1) > 0.99   # run ending here (leftwards)
dark = (s_ < 3 * 75)
ul_, ur_ = [], []
for v in range(760, 1046, 2):
    xs = np.nonzero(run[v, 240:650])[0]
    ys = np.nonzero(runl[v, 650:1035])[0]
    if len(xs):
        l = 240 + int(xs.min())
        # sub-pixel: chroma crossing of 0.45 between l-1 and l
        c0, c1 = chrom[v, l - 1], chrom[v, l]
        ls = l - 1 + (0.45 - c0) / (c1 - c0) if c1 != c0 else float(l)
        ul_.append([v, float(ls), int(dark[v, max(l - 8, 0):l].mean() > 0.5)])
    if len(ys):
        r = 650 + int(ys.max())
        c0, c1 = chrom[v, r], chrom[v, r + 1]
        rs = r + (c0 - 0.45) / (c0 - c1) if c1 != c0 else float(r)
        ur_.append([v, float(rs), int(dark[v, r + 1:r + 9].mean() > 0.5)])
out["uw_left_auto"], out["uw_right_auto"] = ul_, ur_
# boot-top at the stem: top edge of the blue band, column 650 +- 6
Lum = a.mean(2)
c = Lum[400:700, 644:657].mean(1)
k = np.nonzero((c[1:] < 110) & (c[:-1] >= 110))[0]
out["bt_stem_v"] = float(400 + k[0] + 0.5) if len(k) else None
uw.save_json(out, uw.OUT + "/traces/t9388_auto.json")
print({k: (len(v) if isinstance(v, list) else v) for k, v in out.items()})
