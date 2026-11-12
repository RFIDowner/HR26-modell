"""grid.py IMG x0 y0 x1 y1 scale step out.png [lo] -> crop of the upright photo with a labelled pixel grid (full-res coords)."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
PH = r"C:/Users/stig/Documents/Seilbåt"
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/undervann/view"
name = sys.argv[1]; x0, y0, x1, y1 = map(int, sys.argv[2:6]); sc = float(sys.argv[6]); step = int(sys.argv[7]); out = sys.argv[8]
im = ImageOps.exif_transpose(Image.open(f"{PH}/{name}.jpeg")).convert("RGB").crop((x0, y0, x1, y1))
if len(sys.argv) > 9:
    lo = float(sys.argv[9]); a = np.asarray(im).astype(float); L = a.mean(2)
    s = np.clip((L - lo) / (255 - lo), 0, 1) * 255; im = Image.fromarray(s.astype(np.uint8)).convert("RGB")
im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
d = ImageDraw.Draw(im)
f = ImageFont.truetype("arial.ttf", 12)
gx = (x0 // step + 1) * step
while gx < x1:
    X = (gx - x0) * sc
    d.line([(X, 0), (X, im.height)], fill=(255, 0, 255) if gx % (step * 5) == 0 else (0, 255, 255), width=1)
    d.text((X + 2, 2), str(gx), fill=(255, 255, 0), font=f, stroke_width=1, stroke_fill=(0, 0, 0))
    gx += step
gy = (y0 // step + 1) * step
while gy < y1:
    Y = (gy - y0) * sc
    d.line([(0, Y), (im.width, Y)], fill=(255, 0, 255) if gy % (step * 5) == 0 else (0, 255, 255), width=1)
    d.text((2, Y + 1), str(gy), fill=(255, 255, 0), font=f, stroke_width=1, stroke_fill=(0, 0, 0))
    gy += step
im.save(f"{OUT}/{out}")
print(im.size)
