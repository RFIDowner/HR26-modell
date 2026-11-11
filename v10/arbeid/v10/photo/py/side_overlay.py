"""Render baseline with the fitted IMG_9370 orthographic camera; overlay model features and photo measurements."""
import sys, json, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/py")
from stl import load_full
from cam import raster_uv, face_normals
from cam9370 import proj, P9370, hbf, sheer, strake, inv
from PIL import Image, ImageDraw, ImageFont
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
V, F = load_full()
rho, su, sv, u0, v0, th, ph = P9370
t, f = np.radians(th), np.radians(ph)
uv = proj(V)
d = np.array([np.sin(t) * np.cos(f), -np.cos(t) * np.cos(f), -np.sin(f)])
depth = V @ d + 1e5
W, H = 1038, 1552
fid, zb = raster_uv(uv, depth, F, W, H)
mask = fid >= 0
fn = face_normals(V, F)
np.savez_compressed(f"{D}/render_s9370.npz", fid=fid)
# model shading for a side-by-side
cam_back = -d
n = fn[fid[mask]]
n[(n @ cam_back) < 0] *= -1
L = np.array([0.3, 0.8, 0.5]); L /= np.linalg.norm(L)
sh = np.zeros(fid.shape); sh[mask] = 0.3 + 0.7 * np.clip(n @ L, 0, 1)
# silhouette contour of model
edge = mask & ~(np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1))
photo = Image.open(f"{D}/up/IMG_9370.png").convert("RGB")
x0, y0, x1, y1 = 120, 1120, 1010, 1360
SC = 1.6


def T(p):
    return ((p[0] - x0) * SC, (p[1] - y0) * SC)


crop = photo.crop((x0, y0, x1, y1)).resize((int((x1 - x0) * SC), int((y1 - y0) * SC)), Image.LANCZOS)
dr = ImageDraw.Draw(crop)
ey, ex = np.nonzero(edge[y0:y1, x0:x1])
for yy, xx in zip(ey, ex):
    X, Y = xx * SC, yy * SC
    dr.point((X, Y), fill=(255, 40, 40))
# model features
xs = np.linspace(200, 7860, 300)
yy = hbf(xs) - 20
def poly(P3, col, w=2):
    pts = [T(p) for p in proj(P3)]
    dr.line(pts, fill=col, width=w)
poly(np.c_[xs, yy, strake(xs) + 47.5], (255, 150, 0))
poly(np.c_[xs, yy, strake(xs) - 47.5], (255, 150, 0))
xd = np.linspace(0, 7891, 300)
poly(np.c_[xd, hbf(xd), sheer(xd)], (255, 0, 255))
# model window outline (rounded rect in x-z on hull side)
def rrect(xa, xb, za, zb_, r, n=12):
    pts = []
    for cx, cz, a0 in ((xb - r, zb_ - r, 0), (xa + r, zb_ - r, 90), (xa + r, za + r, 180), (xb - r, za + r, 270)):
        for a in np.radians(np.linspace(a0, a0 + 90, n)):
            pts.append((cx + r * np.cos(a), cz + r * np.sin(a)))
    pts.append(pts[0]); return np.array(pts)
W0, W1 = 3700.0, 4900.0
xm = 0.5 * (W0 + W1)
za = float(strake(xm)) + 70; zb_ = float(sheer(xm)) - 30
rr = rrect(W0, W1, za, zb_, 55.0)
poly(np.c_[rr[:, 0], hbf(rr[:, 0]) - 10, rr[:, 1]], (255, 40, 40), 2)
# photo measurements
m = json.load(open(f"{D}/m9370_strake.json"))["strake"]
S = np.array(m)
for col_i, colr in ((1, (0, 220, 255)), (2, (0, 220, 255))):
    pts = [T((r[0], r[col_i])) for r in S[::3]]
    dr.line(pts, fill=colr, width=1)
bt = np.array(json.load(open(f"{D}/m9370_bt.json"))["bt"])
btf = bt[(bt[:, 1] > 1300) & (bt[:, 1] < 1333)]
from scipy.ndimage import median_filter
yb = median_filter(btf[:, 1], 9)
dr.line([T((u, v)) for u, v in zip(btf[::3, 0], yb[::3])], fill=(255, 255, 0), width=2)
# photo window outline (traced)
win = [(577.5, 1236), (579, 1229), (584, 1224.5), (592, 1222.5), (700, 1222), (728, 1222), (737, 1224), (743, 1229), (745.5, 1237), (744, 1244), (738, 1247.5), (700, 1248.3), (600, 1248), (586, 1247), (580, 1243), (577.5, 1236)]
dr.line([T(p) for p in win], fill=(0, 255, 0), width=2)
try:
    fnt = ImageFont.truetype("arial.ttf", 15)
except Exception:
    fnt = ImageFont.load_default()
leg = [((255, 40, 40), "red: today's hull (baseline_fine) silhouette + window, projected with the fitted camera"),
       ((255, 150, 0), "orange: today's rub rail band (95 mm, centre strake_z)"),
       ((255, 0, 255), "magenta: today's deck edge DECK_EDGE_Z"),
       ((0, 220, 255), "cyan: photo rub rail band edges (visible ~4.3 px = ~43 mm)"),
       ((0, 255, 0), "green: photo window frame  x 4010-5620, z 905-1160 fwd"),
       ((255, 255, 0), "yellow: photo boot-top top edge")]
for i, (c, s) in enumerate(leg):
    dr.rectangle([8, 8 + i * 19, 22, 20 + i * 19], fill=c)
    dr.text((28, 6 + i * 19), s, fill=(255, 255, 255), font=fnt, stroke_width=2, stroke_fill=(0, 0, 0))
crop.save(f"{D}/A_side_IMG9370_overlay.png")
print(crop.size)
# model render image same crop for side-by-side
sim = (np.clip(sh[y0:y1, x0:x1], 0, 1) * 255).astype(np.uint8)
sim[~mask[y0:y1, x0:x1]] = 30
Image.fromarray(sim).resize(crop.size, Image.LANCZOS).save(f"{D}/A_side_model_render.png")
