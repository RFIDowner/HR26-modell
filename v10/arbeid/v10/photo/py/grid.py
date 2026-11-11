"""grid.py IMG x0 y0 x1 y1 scale step out.png  -> crop of upright photo with labelled pixel grid (original coords)"""
import sys
from PIL import Image, ImageDraw, ImageFont
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
name = sys.argv[1]; x0, y0, x1, y1 = map(int, sys.argv[2:6]); sc = float(sys.argv[6]); step = int(sys.argv[7]); out = sys.argv[8]
im = Image.open(f"{D}/up/{name}.png").convert("RGB").crop((x0, y0, x1, y1))
im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
d = ImageDraw.Draw(im)
try:
    f = ImageFont.truetype("arial.ttf", 12)
except Exception:
    f = ImageFont.load_default()
gx = (x0 // step + 1) * step
while gx < x1:
    X = (gx - x0) * sc
    d.line([(X, 0), (X, im.height)], fill=(255, 0, 255) if gx % (step * 5) == 0 else (0, 255, 255), width=1)
    d.text((X + 2, 2), str(gx), fill=(255, 255, 0), font=f)
    gx += step
gy = (y0 // step + 1) * step
while gy < y1:
    Y = (gy - y0) * sc
    d.line([(0, Y), (im.width, Y)], fill=(255, 0, 255) if gy % (step * 5) == 0 else (0, 255, 255), width=1)
    d.text((2, Y + 1), str(gy), fill=(255, 255, 0), font=f)
    gy += step
im.save(f"{D}/crops/{out}")
print(im.size)
