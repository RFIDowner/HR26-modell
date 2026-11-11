import json, numpy as np
from PIL import Image
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
a = np.asarray(Image.open(f"{D}/up/IMG_9391.png").convert("RGB")).astype(float)
L = a.mean(2)
rows = []
prev = None
for u in range(0, 1300, 2):
    lo_v, hi_v = 15, 260
    col = L[lo_v:hi_v, u]
    dark = col < 70
    # find runs of dark
    runs = []
    k = 0
    while k < len(col):
        if dark[k]:
            j = k
            while j < len(col) and dark[j]:
                j += 1
            runs.append((k, j)); k = j
        else:
            k += 1
    runs = [r for r in runs if r[1] - r[0] >= 6]
    if not runs:
        continue
    if prev is not None:
        runs.sort(key=lambda r: abs(0.5 * (r[0] + r[1]) + lo_v - prev))
    r = runs[0]
    c = 0.5 * (r[0] + r[1]) + lo_v
    if prev is not None and abs(c - prev) > 12:
        continue
    prev = c
    rows.append([u, r[0] + lo_v, r[1] + lo_v, c])
S = np.array(rows)
print("n", len(S))
for u in (0, 50, 100, 150, 200, 300, 400, 500, 560, 700, 800, 900, 1000, 1100, 1150, 1200, 1240, 1270, 1290):
    i = np.argmin(abs(S[:, 0] - u)); print("u %4d top %3d bot %3d ctr %.1f thick %d" % (S[i, 0], S[i, 1], S[i, 2], S[i, 3], S[i, 2] - S[i, 1]))
json.dump({"strake": S.tolist()}, open(f"{D}/m9391_strake.json", "w"))
