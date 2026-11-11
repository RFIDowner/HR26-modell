"""Boot-top band edges and water contact line along IMG_9370."""
import json, numpy as np
from PIL import Image
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
a = np.asarray(Image.open(f"{D}/up/IMG_9370.png").convert("RGB")).astype(float)
L = a.mean(2); R, G, B = a[..., 0], a[..., 1], a[..., 2]
rows = []
for u in range(236, 985):
    colL = L[1280:1345, u]; colR = R[1280:1345, u]; colB = B[1280:1345, u]
    # white hull: L>200 ; top of boot-top: last white pixel before L<150 (search from top)
    wh = np.nonzero(colL > 200)[0]
    if len(wh) == 0:
        continue
    # contiguous white from the top region
    k = wh[-1]
    # ensure white run above
    if k < 3:
        continue
    # half-level crossing between k and k+1..
    nxt = colL[k + 1:k + 6]
    if len(nxt) == 0 or nxt.min() > 160:
        continue
    lo = nxt.min(); half = 0.5 * (colL[max(k - 3, 0):k + 1].max() + lo)
    kk = k
    while kk + 1 < len(colL) and colL[kk + 1] > half:
        kk += 1
    t = kk + (colL[kk] - half) / (colL[kk] - colL[kk + 1] + 1e-9)
    # below the top edge: blue band (B-R > -5), then red (R-B>30), then water (dark, L<70 and R-B small) 
    sub_r = colR[kk + 1:]; sub_b = colB[kk + 1:]; sub_l = colL[kk + 1:]
    red = np.nonzero((sub_r - sub_b) > 35)[0]
    bt_bot = kk + 1 + red[0] if len(red) else np.nan
    rows.append([u, 1280 + t, 1280 + bt_bot if bt_bot == bt_bot else np.nan])
rows = np.array(rows)
# water contact: below the red/blue, first row where both R and B are low and fairly uniform? use: last row with (R-B)>35 (red line) + 1
wc = []
for u in range(236, 985):
    colR = R[1295:1345, u]; colB = B[1295:1345, u]; colL = L[1295:1345, u]
    red = np.nonzero((colR - colB) > 35)[0]
    if len(red):
        wc.append([u, 1295 + red[-1] + 0.5, 1295 + red[0] - 0.5])
wc = np.array(wc)
json.dump({"bt": rows.tolist(), "red": wc.tolist()}, open(f"{D}/m9370_bt.json", "w"))
for u in (240, 260, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 880, 900, 920, 940, 960):
    i = np.argmin(abs(rows[:, 0] - u)); j = np.argmin(abs(wc[:, 0] - u)) if len(wc) else 0
    print("u %d bt_top %.1f bt_bot(red start) %.1f | red rows %.1f..%.1f" % (rows[i, 0], rows[i, 1], rows[i, 2], wc[j, 2], wc[j, 1]))
