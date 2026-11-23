"""Boot-top top edge in IMG_9388 -> back-project onto plane z=zbt with fitted camera -> waterline half-breadth near bow."""
import sys, json, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/py")
from cam import generic_rot
from slicer import half_breadth
from PIL import Image
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
a = np.asarray(Image.open(f"{D}/up/IMG_9388.png").convert("RGB")).astype(float)
L = a.mean(2); R, B = a[..., 0], a[..., 2]
pts = []
for u in list(range(275, 640, 5)) + list(range(660, 1010, 5)):
    col = L[480:820, u]; bl = (B[480:820, u] - R[480:820, u])
    # white hull above (L>150), then dark blue (L<90 and B>R)
    k = None
    for j in range(3, len(col) - 3):
        if col[j - 3:j].min() > 140 and col[j:j + 3].max() < 100 and bl[j:j + 3].mean() > 5:
            k = j; break
    if k is None:
        continue
    hi = col[k - 3:k].mean(); lo = col[k:k + 3].mean(); half = 0.5 * (hi + lo)
    jj = k - 2
    while jj < k + 2 and col[jj + 1] > half:
        jj += 1
    t = jj + (col[jj] - half) / (col[jj] - col[jj + 1] + 1e-9)
    pts.append([u, 480 + t])
pts = np.array(pts)
fit = json.load(open(f"{D}/fit9388.json")); p = fit["p"]
f, Xc, Yc, Zc, yaw, pitch, roll = p
fwd = np.array([np.cos(np.radians(pitch)) * np.cos(np.radians(yaw)), np.cos(np.radians(pitch)) * np.sin(np.radians(yaw)), np.sin(np.radians(pitch))])
Rm = generic_rot(fwd, roll=roll); C = np.array([Xc, Yc, Zc])
W, H = 1500, 2000
out = []
for zbt in (110.0, 130.0, 150.0):
    res = []
    for u, v in pts:
        dcam = np.array([(u - W / 2) / f, -(v - H / 2) / f, -1.0])   # right, up, back coords -> back = -1 (looking forward)
        dw = Rm.T @ dcam
        s = (zbt - C[2]) / dw[2]
        X = C + s * dw
        res.append([u, v, X[0], X[1]])
    res = np.array(res)
    out.append(res)
    print("zbt", zbt)
    for xq in (900, 1200, 1500, 1800, 2100, 2400):
        for side, sel in (("L", res[:, 3] > 0), ("R", res[:, 3] < 0)):
            r = res[sel]
            if len(r) < 3:
                continue
            o = np.argsort(r[:, 2]); yv = np.interp(xq, r[o, 2], np.abs(r[o, 3]), left=np.nan, right=np.nan)
            print("   x %5d %s photo hb %.0f  model hb(z=%d) %.0f" % (xq, side, yv, zbt, half_breadth(xq, zbt)))
json.dump({"pts": pts.tolist(), "bp130": out[1].tolist()}, open(f"{D}/bt9388.json", "w"))
print("n pts", len(pts), pts[::8].round(1).tolist())
