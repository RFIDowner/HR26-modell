import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
from PIL import Image, ImageDraw
from lib import OUT, font
im = Image.open("C:/Users/stig/Documents/GitHub/HR26-modell/docs/images/overlegg-profil.jpg").convert("RGB")
PX = 3.27   # mm full scale per px in overlegg-profil.jpg (bow 2510 px, stern ~80 px, LOA 7950)
def X(xf): return 2510 - xf / PX           # x from bow -> image column
def crop(box, z):
    c = im.crop(box); return c.resize((int(c.width * z), int(c.height * z)), Image.LANCZOS), box, z
def arrow(dr, p, q, col, w=3):
    dr.line([p, q], fill=col, width=w)
    import math
    a = math.atan2(q[1] - p[1], q[0] - p[0])
    for s in (-0.5, 0.5):
        dr.line([q, (q[0] - 14 * math.cos(a + s), q[1] - 14 * math.sin(a + s))], fill=col, width=w)
def tb(dr, xy, t, col=(0, 0, 0), size=16):
    f = font(size); bb = dr.textbbox(xy, t, font=f)
    dr.rectangle([bb[0] - 3, bb[1] - 2, bb[2] + 3, bb[3] + 2], fill=(255, 255, 255)); dr.text(xy, t, font=f, fill=col)
panels = []
# 1 bow
c, box, z = crop((2190, 220, 2560, 470), 2.1)
dr = ImageDraw.Draw(c)
tb(dr, (8, 8), "Bow: red block = anchor_roller() 520 x 170, top +140 over deck, bottom 420 below", (150, 0, 0))
tb(dr, (8, 32), "its lower front corner is 107 mm (3.6 mm model) ahead of the stem at z=793", (150, 0, 0))
tb(dr, (8, 56), "drawing: no tall block on the foredeck; strake line ends in a small fitting ~100 mm ahead of the stem", (0, 0, 0))
p = ((X(170) - box[0]) * z, (424 - box[1]) * z)
arrow(dr, (p[0] + 120, p[1] + 60), (p[0] + 4, p[1] + 2), (200, 0, 0))
panels.append(c)
# 2 coachroof front
c, box, z = crop((1720, 215, 1900, 320), 4.0)
dr = ImageDraw.Draw(c)
tb(dr, (8, 8), "Coachroof front: model (red) is a VERTICAL wall at x=2200", (150, 0, 0))
tb(dr, (8, 32), "drawing: ~48 deg slope 2197 -> 2322 (README says 45 deg)", (0, 0, 0))
panels.append(c)
# 3 sprayhood
c, box, z = crop((580, 105, 1060, 345), 1.6)
dr = ImageDraw.Draw(c)
tb(dr, (8, 8), "Sprayhood: model = box 5135-6150, vertical front and back", (150, 0, 0))
tb(dr, (8, 32), "drawing (dashed): top 5144-5978, front raked to ~4905, round aft hoop", (0, 0, 0))
panels.append(c)
# 4 stern cleat
c, box, z = crop((60, 300, 330, 400), 2.6)
dr = ImageDraw.Draw(c)
tb(dr, (8, 8), "Stern: cleat 260 x 90 x 100 mm (8.7 x 3 x 3.3 mm model) stands", (150, 0, 0))
tb(dr, (8, 32), "above every line of the drawing; strake/name relief bumps at transom", (150, 0, 0))
panels.append(c)
Wd = 1600
H = 46 + sum(int(p.height * min(1.0, (Wd - 20) / p.width)) + 16 for p in panels)
out = Image.new("RGB", (Wd, H), (255, 255, 255)); d = ImageDraw.Draw(out)
d.text((10, 10), "Model silhouette (red) on the 1:50 profile drawing (docs/images/overlegg-profil.jpg), zoomed", font=font(19), fill=(0, 0, 0))
y = 46
for p in panels:
    s = min(1.0, (Wd - 20) / p.width)
    q = p.resize((int(p.width * s), int(p.height * s)), Image.LANCZOS) if s < 1 else p
    out.paste(q, (10, y)); d.rectangle([10, y, 10 + q.width - 1, y + q.height - 1], outline=(170, 170, 170)); y += q.height + 16
out.save(OUT + "/edges_vs_drawing.png"); print(out.size)
