import numpy as np
from PIL import Image, ImageDraw, ImageFont
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
try:
    f = ImageFont.truetype("arial.ttf", 17); fb = ImageFont.truetype("arialbd.ttf", 18)
except Exception:
    f = fb = ImageFont.load_default()
def lab(dr, xy, text, col=(255, 255, 0), anchor=None):
    dr.text(xy, text, fill=col, font=f, stroke_width=3, stroke_fill=(0, 0, 0))
# ---- D: deck from above (IMG_9372 crop 170..800 x 1180..1760, scale 1.6)
im = Image.open(f"{D}/up/IMG_9372.png").convert("RGB")
x0, y0, x1, y1, S = 170, 1190, 800, 1760, 1.6
c = im.crop((x0, y0, x1, y1)).resize((int((x1 - x0) * S), int((y1 - y0) * S)), Image.LANCZOS)
dr = ImageDraw.Draw(c)
T = lambda x, y: ((x - x0) * S, (y - y0) * S)
def box(xa, ya, xb, yb, col):
    dr.rectangle([T(xa, ya), T(xb, yb)], outline=col, width=3)
box(558, 1298, 628, 1342, (0, 255, 255)); lab(dr, T(632, 1290), "forehatch on coachroof, fwd of mast", (0, 255, 255))
dr.ellipse([T(545, 1360), T(560, 1376)], outline=(255, 0, 255), width=3); lab(dr, T(565, 1352), "mast foot", (255, 0, 255))
dr.ellipse([T(318, 1392), T(530, 1555)], outline=(255, 255, 0), width=3)
lab(dr, T(330, 1372), "sprayhood: soft dome, raked front, rounded aft hoop", (255, 255, 0))
dr.line([T(250, 1545), T(470, 1560), T(495, 1650)], fill=(0, 255, 0), width=3)
lab(dr, T(180, 1500), "cockpit coaming: low, rounded, runs into aft deck", (0, 255, 0))
dr.line([T(625, 1530), T(680, 1415)], fill=(255, 128, 0), width=4); lab(dr, T(690, 1440), "hull window\n(stbd)", (255, 128, 0))
dr.line([T(700, 1300), T(640, 1530), T(560, 1650), T(450, 1690)], fill=(80, 160, 255), width=2)
lab(dr, T(560, 1690), "rub rail wraps round stern quarter", (80, 160, 255))
lab(dr, T(190, 1715), "transom + bathing ladder", (255, 255, 255))
c.save(f"{D}/D_deck_IMG9372_annot.png"); print("D", c.size)
# ---- E: details composite: window/rail (IMG_9387), stem (IMG_9388), bow rail end (IMG_9395)
a = Image.open(f"{D}/up/IMG_9387.png").convert("RGB").crop((1280, 230, 1660, 430)).resize((760, 400), Image.LANCZOS)
da = ImageDraw.Draw(a)
lab(da, (8, 6), "IMG_9387: window fwd end (semicircular), raised grey frame,\nrub rail = dark D-profile ~0.25x window frame height")
b = Image.open(f"{D}/up/IMG_9388.png").convert("RGB").crop((560, 150, 740, 560)).resize((270, 615), Image.LANCZOS)
db = ImageDraw.Draw(b)
db.line([(int((620 - 560) * 1.5), 300), (int((675 - 560) * 1.5), 300)], fill=(255, 255, 0), width=3)
lab(db, (5, 6), "IMG_9388 stem:\nrounded band\n~50 px = ~45-55 mm\n-> R ~30 mm")
cimg = Image.open(f"{D}/up/IMG_9395.png").convert("RGB").crop((1300, 350, 2300, 1200)).resize((560, 476), Image.LANCZOS)
dc = ImageDraw.Draw(cimg)
lab(dc, (6, 6), "IMG_9395: rail runs right to stem head\n(no flat end), anchor on roller above")
Wt = a.width + b.width + 10
comp = Image.new("RGB", (max(Wt, cimg.width + b.width + 10), 400 + 476 + 10), (30, 30, 30))
comp.paste(a, (0, 0)); comp.paste(b, (a.width + 10, 0)); comp.paste(cimg, (0, 410))
comp.save(f"{D}/E_details_window_rail_stem.png"); print("E", comp.size)
