"""Extract stem/transom outlines and window, boot-top in IMG_9370."""
import sys, json, numpy as np
from PIL import Image
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
a = np.asarray(Image.open(f"{D}/up/IMG_9370.png").convert("RGB")).astype(float)
L = a.mean(2)
res = {}
# stem outline: for rows v 1224..1330, first u (from left, starting at 120) where L>235 sustained 4 px
stem = []
for v in range(1223, 1331):
    row = L[v, 120:330]
    ok = np.nonzero((row[:-4] > 228) & (row[1:-3] > 228) & (row[2:-2] > 228) & (row[3:-1] > 228))[0]
    if len(ok):
        k = ok[0]
        # subpixel: half level between k-1 and k
        lo = row[max(k - 3, 0):k].min() if k > 0 else row[k]
        half = 0.5 * (lo + 245)
        kk = k
        while kk > 0 and row[kk - 1] > half:
            kk -= 1
        sub = kk - 1 + (half - row[kk - 1]) / (row[kk] - row[kk - 1] + 1e-9) if kk > 0 else kk
        stem.append([120 + sub, v])
res["stem"] = stem
# transom outline: for rows v 1215..1300, last u (scan from right 1010 to 880) with L>220
tr = []
for v in range(1212, 1300):
    row = L[v, 880:1012]
    ok = np.nonzero((row[1:] > 215) & (row[:-1] > 215))[0]
    if len(ok):
        k = ok[-1] + 1
        hi = 245; lo = row[min(k + 1, len(row) - 1):min(k + 4, len(row))].min() if k + 1 < len(row) else row[k]
        half = 0.5 * (hi + lo)
        kk = k
        while kk < len(row) - 1 and row[kk + 1] > half:
            kk += 1
        sub = kk + (row[kk] - half) / (row[kk] - row[kk + 1] + 1e-9) if kk < len(row) - 1 else kk
        tr.append([880 + sub, v])
res["transom"] = tr
# hull top (bow) : for columns 152..176 find top of white hull (dark above)
top = []
for u in range(152, 178):
    col = L[1195:1232, u]
    ok = np.nonzero((col[:-3] > 228) & (col[1:-2] > 228) & (col[2:-1] > 228))[0]
    if len(ok):
        k = ok[0]
        if k > 0:
            half = 0.5 * (col[:k].min() + 245)
            kk = k
            while kk > 0 and col[kk - 1] > half:
                kk -= 1
            sub = kk - 1 + (half - col[kk - 1]) / (col[kk] - col[kk - 1] + 1e-9)
            top.append([u, 1195 + sub])
res["bowtop"] = top
json.dump(res, open(f"{D}/m9370_outl.json", "w"))
st = np.array(stem); trr = np.array(tr); tp = np.array(top)
print("stem:", st[::8].round(1).tolist())
print("transom:", trr[::6].round(1).tolist())
print("bowtop:", tp.round(1).tolist())
