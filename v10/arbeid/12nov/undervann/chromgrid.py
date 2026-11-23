"""chromgrid.py IMG x0 y0 x1 y1 scale step out.png [lo hi]: red-chromaticity crop with a pixel grid"""
import sys
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/undervann/py")
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import uw
name = sys.argv[1]; x0, y0, x1, y1 = map(int, sys.argv[2:6]); sc = float(sys.argv[6]); step = int(sys.argv[7]); out = sys.argv[8]
lo, hi = (float(sys.argv[9]), float(sys.argv[10])) if len(sys.argv) > 10 else (0.30, 0.65)
a = uw.photo(name).astype(float)[y0:y1, x0:x1]
r = a[..., 0] / (a.sum(2) + 1.0)
g = np.clip((r - lo) / (hi - lo), 0, 1) * 255
L = np.clip(a.mean(2) * 1.0, 0, 255)
im = Image.fromarray(np.dstack([g, 0.5 * L, 0.5 * L]).astype(np.uint8))
im = im.resize((int(im.width * sc), int(im.height * sc)), Image.NEAREST)
d = ImageDraw.Draw(im)
f = ImageFont.truetype("arial.ttf", 11)
gx = (x0 // step + 1) * step
while gx < x1:
    X = (gx - x0) * sc
    d.line([(X, 0), (X, im.height)], fill=(255, 255, 0) if gx % (step * 5) == 0 else (0, 120, 255), width=1)
    if gx % (step * 2) == 0:
        d.text((X + 2, 2), str(gx), fill=(255, 255, 255), font=f)
    gx += step
gy = (y0 // step + 1) * step
while gy < y1:
    Y = (gy - y0) * sc
    d.line([(0, Y), (im.width, Y)], fill=(255, 255, 0) if gy % (step * 5) == 0 else (0, 120, 255), width=1)
    if gy % (step * 2) == 0:
        d.text((2, Y + 1), str(gy), fill=(255, 255, 255), font=f)
    gy += step
im.save(uw.OUT + "/view/" + out)
print(im.size)
