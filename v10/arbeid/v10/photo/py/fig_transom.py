import json, numpy as np
from PIL import Image, ImageDraw, ImageFont
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
im = Image.open(f"{D}/up/IMG_9391.png").convert("RGB").crop((0, 0, 1500, 1000))
dr = ImageDraw.Draw(im)
try:
    fnt = ImageFont.truetype("arial.ttf", 24); fs = ImageFont.truetype("arial.ttf", 20)
except Exception:
    fnt = fs = ImageFont.load_default()
S = np.array(json.load(open(f"{D}/m9391_strake.json"))["strake"])
S = S[(S[:, 0] <= 560) | (S[:, 0] >= 700)]
c = np.where(S[:, 0] >= 950, S[:, 1] + 13.0, S[:, 3])
seg1 = [(u, v) for u, v in zip(S[:, 0], c) if u <= 560]
seg2 = [(u, v) for u, v in zip(S[:, 0], c) if u >= 700 and u <= 1240]
dr.line(seg1, fill=(0, 255, 255), width=3); dr.line(seg2, fill=(0, 255, 255), width=3)
# chord + sagitta of strake across transom (apex ~ (590,47))
dr.line([(0, 145), (1240, 166)], fill=(255, 0, 255), width=2)
# boot-top straight part and ends
dr.line([(300, 656.5), (1000, 656.5)], fill=(255, 255, 0), width=4)
dr.line([(160, 700), (215, 677), (300, 657)], fill=(255, 200, 0), width=3)
dr.line([(1000, 657), (1045, 668), (1080, 690)], fill=(255, 200, 0), width=3)
# outline right & left (read from fine grid)
R = [(1290, 215), (1265, 250), (1255, 300), (1232, 400), (1215, 450), (1195, 500), (1175, 550), (1150, 600), (1120, 650), (1090, 700), (1065, 725)]
Lf = [(30, 450), (60, 500), (88, 550), (110, 600), (133, 650), (158, 700), (178, 730)]
dr.line(R, fill=(0, 255, 0), width=4); dr.line(Lf, fill=(0, 255, 0), width=4)
# centreline
dr.line([(640, 0), (640, 1000)], fill=(255, 255, 255), width=1)
txt = [((0, 255, 255), "cyan: rub rail centre across transom; apex ~v47 at centre, drops 119 px at the stbd corner (u1240)"),
       ((255, 0, 255), "magenta: chord corner-to-corner -> rail arches ~100 px above it (plan camber + view from below)"),
       ((255, 255, 0), "yellow: boot-top top edge, dead straight over u 300-1000 (central ~55% of rail width)"),
       ((255, 200, 0), "orange: boot-top turns down round soft corners (no knuckle)"),
       ((0, 255, 0), "green: hull outline seen from astern: smooth convex U, no hard transom edge")]
for i, (col, s) in enumerate(txt):
    dr.rectangle([12, 760 + i * 34, 36, 784 + i * 34], fill=col)
    dr.text((44, 758 + i * 34), s, fill=(255, 255, 255), font=fs, stroke_width=3, stroke_fill=(0, 0, 0))
im.save(f"{D}/C_transom_IMG9391_annot.png")
print(im.size)
