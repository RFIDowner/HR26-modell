"""Klipper ut et utsnitt av tegningen og forstorrer det.
Bruk: python -I crop.py <bilde> <ut.png> x0 y0 x1 y1 [skala] [grid]
Koordinater i originale piksler. grid>0 tegner rutenett med den avstanden."""
import sys
from PIL import Image, ImageDraw, ImageOps

src, out = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = [int(v) for v in sys.argv[3:7]]
sc = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
grid = int(sys.argv[8]) if len(sys.argv) > 8 else 0
im = Image.open(src).convert("RGB")
c = im.crop((x0, y0, x1, y1))
if sc != 1.0:
    c = c.resize((int(c.width * sc), int(c.height * sc)), Image.LANCZOS)
if grid:
    d = ImageDraw.Draw(c)
    g0x = (x0 // grid + 1) * grid
    for gx in range(g0x, x1, grid):
        X = (gx - x0) * sc
        d.line([(X, 0), (X, c.height)], fill=(255, 0, 0) if gx % (grid * 5) == 0 else (255, 160, 160), width=1)
        d.text((X + 2, 2), str(gx), fill=(200, 0, 0))
    g0y = (y0 // grid + 1) * grid
    for gy in range(g0y, y1, grid):
        Y = (gy - y0) * sc
        d.line([(0, Y), (c.width, Y)], fill=(0, 0, 255) if gy % (grid * 5) == 0 else (160, 160, 255), width=1)
        d.text((2, Y + 2), str(gy), fill=(0, 0, 200))
c.save(out)
print(out, c.size)
