import sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
r = np.load(f"{D}/render_b9388.npz"); fid = r["fid"]; sh = r["shade"]
mask = fid >= 0
# model right silhouette per row
H, W = mask.shape
msil = []
for v in range(0, 1000, 2):
    xs = np.nonzero(mask[v, 648:1300])[0]
    if len(xs):
        msil.append([v, 648 + xs.max()])
msil = np.array(msil)
lsil = []
for v in range(0, 1000, 2):
    xs = np.nonzero(mask[v, 0:648])[0]
    if len(xs):
        lsil.append([v, xs.min()])
lsil = np.array(lsil)
psil = np.array([[400, 1091], [440, 1094], [480, 1095], [520, 1094], [560, 1092], [600, 1086], [620, 1080], [635, 1075], [640, 1073], [660, 1072], [680, 1071], [700, 1069], [720, 1066], [740, 1063], [760, 1058], [780, 1052.5], [800, 1047]])
m9388 = json.load(open(f"{D}/m9388.json"))
pl = np.array(m9388["left"]); pl = pl[pl[:, 0] <= 600]
for v in (0, 200, 400, 500, 600, 640, 700, 760, 800, 840):
    i = np.argmin(abs(msil[:, 0] - v)); j = np.argmin(abs(psil[:, 0] - v)) if v >= 400 else None
    print("row %d model R-sil %d  photo R-sil %s" % (v, msil[i, 1], psil[j, 1] if j is not None and abs(psil[j, 0] - v) < 5 else "-"))
photo = Image.open(f"{D}/up/IMG_9388.png").convert("RGB")
img = photo.copy()
dr = ImageDraw.Draw(img)
edge = mask & ~(np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1))
ey, ex = np.nonzero(edge)
for yy, xx in zip(ey, ex):
    dr.ellipse([xx - 1, yy - 1, xx + 1, yy + 1], fill=(255, 30, 30))
dr.line([tuple(p[::-1]) for p in psil], fill=(0, 255, 0), width=4)
dr.line([(p[1], p[0]) for p in pl[::2]], fill=(0, 255, 0), width=3)
bt = json.load(open(f"{D}/bt9388.json"))["pts"]
dr.line([tuple(p) for p in bt], fill=(255, 255, 0), width=3)
try:
    fnt = ImageFont.truetype("arial.ttf", 30)
except Exception:
    fnt = ImageFont.load_default()
for i, (c, s) in enumerate([((255, 30, 30), "red: today's hull silhouette (fitted camera)"), ((0, 255, 0), "green: photo silhouette (rub rail, then hull)"), ((255, 255, 0), "yellow: photo boot-top top edge")]):
    dr.rectangle([20, 1700 + i * 44, 50, 1730 + i * 44], fill=c)
    dr.text((60, 1696 + i * 44), s, fill=(255, 255, 255), font=fnt, stroke_width=3, stroke_fill=(0, 0, 0))
img.crop((0, 0, 1500, 1880)).resize((1200, 1504), Image.LANCZOS).save(f"{D}/B_bow_IMG9388_overlay.png")
# model render panel
sim = (np.clip(sh, 0, 1) * 255).astype(np.uint8); sim[~mask] = 40
Image.fromarray(sim).crop((0, 0, 1500, 1880)).resize((600, 752), Image.LANCZOS).save(f"{D}/B_bow_model_render.png")
json.dump({"model_right_sil": msil.tolist(), "model_left_sil": lsil.tolist(), "photo_right_sil": psil.tolist()}, open(f"{D}/bow_sil_cmp.json", "w"))
