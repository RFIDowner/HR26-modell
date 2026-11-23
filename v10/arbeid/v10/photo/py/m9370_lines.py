"""Extract strake band, boot-top band and waterline along the hull in IMG_9370 (upright pixel coords)."""
import json
import numpy as np
from PIL import Image
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
a = np.asarray(Image.open(f"{D}/up/IMG_9370.png").convert("RGB")).astype(float)
L = a.mean(2)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
out = {"strake": [], "boottop": []}
# strake: darkest run between y 1218..1268 bounded by white hull (L>235) above and below
for u in range(152, 990):
    col = L[1215:1270, u]
    j = int(np.argmin(col)); vmin = col[j]
    if vmin > 190:
        continue
    # local white level above/below
    top_white = np.max(col[max(0, j - 12):j]) if j > 0 else 255
    bot_white = np.max(col[j:j + 14])
    half = vmin + 0.5 * (min(top_white, bot_white) - vmin)
    k0 = j
    while k0 > 0 and col[k0] < half:
        k0 -= 1
    k1 = j
    while k1 < len(col) - 1 and col[k1] < half:
        k1 += 1
    # subpixel edges by linear interpolation
    t = k0 + (half - col[k0]) / (col[k0 + 1] - col[k0] + 1e-9)
    b = k1 - 1 + (half - col[k1 - 1]) / (col[k1] - col[k1 - 1] + 1e-9)
    w = np.clip(half - col[k0 + 1:k1], 0, None)
    c = (np.arange(k0 + 1, k1) * w).sum() / max(w.sum(), 1e-9)
    out["strake"].append([u, 1215 + t, 1215 + b, 1215 + c, float(vmin)])
# boot-top: blue band; find transition white->dark (top) and dark-blue -> red/other (bottom) between 1295..1345
for u in range(200, 975):
    col = L[1290:1345, u]
    # top edge: first y where L drops below 150 after being >220
    idx = np.nonzero(col < 150)[0]
    if len(idx) == 0:
        continue
    k = idx[0]
    if k == 0 or col[:k].max() < 200:
        continue
    hi = col[:k].max(); lo = col[k:k + 6].min(); half = 0.5 * (hi + lo)
    kk = k
    while kk > 0 and col[kk - 1] < half:
        kk -= 1
    t = kk - 1 + (half - col[kk - 1]) / (col[kk] - col[kk - 1] + 1e-9) if kk > 0 else kk
    # blue band: B > R ; red: R > B + 20
    rr = R[1290:1345, u]; bb = B[1290:1345, u]
    blue = (bb - rr) > 5
    red = (rr - bb) > 25
    yb = 1290 + kk
    # bottom of blue: first red pixel below top
    rid = np.nonzero(red[kk:])[0]
    bot = 1290 + kk + rid[0] if len(rid) else np.nan
    out["boottop"].append([u, 1290 + t, float(bot)])
json.dump(out, open(f"{D}/m9370_lines.json", "w"))
s = np.array(out["strake"]); bt = np.array(out["boottop"])
print("strake n", len(s))
for u in (155, 160, 180, 200, 250, 300, 400, 500, 600, 650, 700, 750, 800, 850, 900, 940, 960, 975, 985):
    r = s[np.argmin(abs(s[:, 0] - u))]
    print("u %4d top %.1f bot %.1f ctr %.1f thick %.1f min %.0f" % (r[0], r[1], r[2], r[3], r[2] - r[1], r[4]))
print("boottop n", len(bt))
for u in (220, 250, 300, 400, 500, 600, 700, 800, 850, 900, 940, 960):
    r = bt[np.argmin(abs(bt[:, 0] - u))]
    print("u %4d bt_top %.1f red_start %.1f" % (r[0], r[1], r[2]))
