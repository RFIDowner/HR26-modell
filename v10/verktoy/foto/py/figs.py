import sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '.')
import common as c
W = c.W
B = json.load(open(W + "/out/snap_before.json")); A = json.load(open(W + "/out/snap_after.json"))
def font(sz):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", sz)
    except Exception:
        return ImageFont.load_default()
CB, CA, CE = (0, 170, 255), (230, 0, 160), (0, 160, 0)
# ---------------- Enderlein profile overlay
E = Image.open(c.SRC + "/HR26interior448-5.jpeg").convert("RGB")
S, XB = 4.2591, 2240.1
def ydwl(px): return 541.35 + (px - 290.0) * (542.18 - 541.35) / (2066.0 - 290.0)
def epx(x, zB):
    zE = 0.968 * np.asarray(zB) + 25.5
    px = XB - np.asarray(x) / S
    return px, ydwl(px) - zE / S
box = (330, 380, 2280, 900)
im = E.crop(box); d = ImageDraw.Draw(im)
for prof, col in ((B["profile"], CB), (A["profile"], CA)):
    p = np.array(prof); p = p[p[:, 0] >= 900]
    u, v = epx(p[:, 0], p[:, 1])
    d.line(list(zip(u - box[0], v - box[1])), fill=col, width=3)
# deadwood: canoe keel point line (after)
xs = np.arange(5900, 7800, 20.0)
dwh = np.interp(xs, [5600, 5900, 6800, 7400, 7800, 8000], [0, 0, 100, 170, 210, 210])
pa = np.array(A["profile"]); zp = np.interp(xs, pa[:, 0], pa[:, 1])
u, v = epx(xs, zp + dwh)
for i in range(0, len(u) - 1, 2):
    d.line([(u[i] - box[0], v[i] - box[1]), (u[i + 1] - box[0], v[i + 1] - box[1])], fill=CA, width=2)
f = font(22)
d.text((20, 15), "Enderlein 448-5 (1:15 scan). Model centreline profile mapped into his frame: z_E = 0.968 z_model + 25.5", fill=(0, 0, 0), font=f)
d.text((20, 42), "cyan = before (V10 today), magenta = proposal; dashed magenta = canoe-body keel point above the deadwood", fill=(0, 0, 0), font=f)
im = im.resize((1600, int(im.size[1] * 1600 / im.size[0])), Image.LANCZOS); im.save(W + "/img/ovl_enderlein_profile.png")
# ---------------- brochure overlay (aft part, bcal)
Bi = Image.open(c.OLD + "/enderlein/work/broch_p6_prof.png").convert("RGB"); d = ImageDraw.Draw(Bi)
def bpx(x, z): return 2536.2 - np.asarray(x) / 3.28, 598.6 - np.asarray(z) / 3.28
for prof, col in ((B["profile"], CB), (A["profile"], CA)):
    p = np.array(prof); p = p[p[:, 0] >= 2150]
    u, v = bpx(p[:, 0], p[:, 1]); d.line(list(zip(u, v)), fill=col, width=3)
ux, ud = c.C._read("uw_station.csv", "x_from_bow_mm", "depth_below_DWL_mm")
m = ux >= 2150; u, v = bpx(ux[m], -ud[m])
for a, b in zip(u[::3], v[::3]):
    d.point((a, b), fill=(255, 200, 0))
d.text((20, 960), "Brochure 1:50 profile (aft of x 2150). cyan = before, magenta = proposal, yellow dots = data/uw_station.csv", fill=(0, 0, 0), font=font(26))
Bi = Bi.resize((1600, int(Bi.size[1] * 1600 / Bi.size[0])), Image.LANCZOS); Bi.save(W + "/img/ovl_brochure_profile.png")
# ---------------- body plan
Wd, Hd = 1600, 1000; sc = 0.42
bp = Image.new("RGB", (Wd, Hd), (255, 255, 255)); d = ImageDraw.Draw(bp)
cx, cz = Wd // 2, 120 + int(1250 * sc)
def P2(y, z): return cx + y * sc, cz - z * sc
for z in (0.0,):
    d.line([P2(-1400, z), P2(1400, z)], fill=(150, 150, 150), width=1)
d.line([P2(0, -500), P2(0, 1300)], fill=(150, 150, 150), width=1)
keys = list(A["sections"].keys())
cols = [(int(40 + 200 * i / len(keys)), 0, int(220 - 200 * i / len(keys))) for i in range(len(keys))]
for i, k in enumerate(keys):
    x = float(k); side = 1 if x < 4300 else -1
    for S_, w, col in ((B, 1, (170, 170, 170)), (A, 2, cols[i])):
        p = np.array(S_["sections"][k])
        d.line([P2(side * y, z) for y, z in p], fill=col, width=w)
    pe = np.array(A["sections"][k])[-1]
    d.text(P2(side * (pe[0] + 30) - (60 if side < 0 else 0), pe[1] + 40), f"{int(x)}", fill=cols[i], font=font(16))
d.text((20, 15), "Body plan, full-scale mm (scale 0.42 px/mm). Right: forward stations x < 4300; left: aft stations. Grey = before, colour = proposal.", fill=(0, 0, 0), font=font(20))
d.text((20, 42), "Horizontal line = DWL (z 0). Proposal: V midships/aft (deadrise 16-26 deg at x 4800-6000), firm bilge (N 4.0), deadwood + hollow garboard aft of x 5900.", fill=(0, 0, 0), font=font(20))
bp.save(W + "/img/bodyplan.png")
print("ok")
