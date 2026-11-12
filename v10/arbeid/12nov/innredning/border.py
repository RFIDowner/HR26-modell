"""Finner rammelinjene i skanningen og maaler rotasjon."""
import sys
import numpy as np
from PIL import Image

im = np.asarray(Image.open(sys.argv[1]).convert("L"), dtype=float)
H, W = im.shape
dark = im < 140
# topp- og bunnlinje: for hver kolonne-blokk, finn y med mest moerke piksler i et baand
def hline(y0, y1, xs):
    out = []
    for x in xs:
        col = dark[y0:y1, x - 5:x + 5].sum(axis=1)
        if col.max() >= 3:
            out.append((x, y0 + int(np.argmax(col))))
    return out
def vline(x0, x1, ys):
    out = []
    for y in ys:
        row = dark[y - 5:y + 5, x0:x1].sum(axis=0)
        if row.max() >= 3:
            out.append((y, x0 + int(np.argmax(row))))
    return out
xs = list(range(150, W - 150, 100))
ys = list(range(150, H - 150, 100))
top = hline(10, 80, xs)
bot = hline(H - 90, H - 10, xs)
left = vline(10, 90, ys)
right = vline(W - 90, W - 10, ys)
for name, pts in (("top", top), ("bot", bot)):
    a = np.array(pts, float)
    p = np.polyfit(a[:, 0], a[:, 1], 1)
    print(name, "y = %.5f x + %.1f" % tuple(p), "angle deg %.3f" % np.degrees(np.arctan(p[0])), "resid", np.round(a[:, 1] - np.polyval(p, a[:, 0]), 1).tolist())
for name, pts in (("left", left), ("right", right)):
    a = np.array(pts, float)
    p = np.polyfit(a[:, 0], a[:, 1], 1)
    print(name, "x = %.5f y + %.1f" % tuple(p), "angle deg %.3f" % np.degrees(np.arctan(p[0])), "resid", np.round(a[:, 1] - np.polyval(p, a[:, 0]), 1).tolist())
