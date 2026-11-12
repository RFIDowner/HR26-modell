"""Draw traced pixel polylines on a zoomed crop of the drawing for checking."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
from img import SRC

COLS = [(220, 0, 0), (0, 90, 230), (0, 160, 0), (200, 0, 200), (230, 120, 0), (0, 170, 170)]


def show(lines, box, scale, out, step=10, dots=True, width=1):
    """lines: list of arrays (N, >=2) of pixel coords (x, y)."""
    x0, y0, x1, y1 = box
    im = Image.open(SRC).convert("L").crop(box)
    im = im.resize((int((x1 - x0) * scale), int((y1 - y0) * scale)), Image.LANCZOS).convert("RGB")
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        f = ImageFont.load_default()
    gx = (x0 // step + 1) * step
    while gx < x1:
        X = (gx - x0) * scale
        d.line([(X, 0), (X, 4)], fill=(0, 0, 255))
        if gx % (step * 5) == 0:
            d.text((X + 1, 4), str(gx), fill=(0, 0, 255), font=f)
        gx += step
    gy = (y0 // step + 1) * step
    while gy < y1:
        Y = (gy - y0) * scale
        d.line([(0, Y), (4, Y)], fill=(255, 100, 0))
        if gy % (step * 5) == 0:
            d.text((5, Y - 6), str(gy), fill=(200, 60, 0), font=f)
        gy += step
    for k, L in enumerate(lines):
        c = COLS[k % len(COLS)]
        pts = [((p[0] - x0) * scale, (p[1] - y0) * scale) for p in L
               if x0 <= p[0] <= x1 and y0 <= p[1] <= y1]
        if dots:
            for X, Y in pts:
                d.point((X, Y), fill=c)
        elif len(pts) > 1:
            d.line(pts, fill=c, width=width)
    im.save(out)
    return out
