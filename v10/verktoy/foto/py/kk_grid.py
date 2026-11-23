"""kk_: forstoerret utsnitt med rutenett (originalpiksler) for manuell avlesning.
python kk_grid.py <bilde> <ut.png> u0 v0 u1 v1 zoom [steg]"""
import sys
from PIL import Image, ImageDraw, ImageOps
import kk_lib as L
src, out = sys.argv[1], sys.argv[2]
u0, v0, u1, v1, Z = [int(a) for a in sys.argv[3:8]]
st = int(sys.argv[8]) if len(sys.argv) > 8 else 10
im = Image.open(src).convert("RGB").crop((u0, v0, u1, v1))
if len(sys.argv) > 9:
    im = ImageOps.autocontrast(im, cutoff=1)
im = im.resize(((u1 - u0) * Z, (v1 - v0) * Z), Image.LANCZOS)
dr = ImageDraw.Draw(im)
f = L.font(11)
for u in range((u0 // st + 1) * st, u1, st):
    x = (u - u0) * Z
    dr.line([(x, 0), (x, im.height)], fill=(255, 0, 255) if u % (5 * st) == 0 else (255, 160, 255), width=1)
    if u % (5 * st) == 0:
        dr.text((x + 2, 2), str(u), fill=(255, 0, 255), font=f)
for v in range((v0 // st + 1) * st, v1, st):
    y = (v - v0) * Z
    dr.line([(0, y), (im.width, y)], fill=(0, 160, 255) if v % (5 * st) == 0 else (140, 210, 255), width=1)
    if v % (5 * st) == 0:
        dr.text((2, y + 2), str(v), fill=(0, 120, 255), font=f)
im.save(out)
