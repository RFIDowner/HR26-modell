"""Tile several small zoomed crops (with pixel grid) into one image.

usage: python -I tiles.py out.png scale step "x0,y0,x1,y1" ... [--enh]
"""
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from img import SRC


def tile(box, s, step, enh, f):
    x0, y0, x1, y1 = box
    im = Image.open(SRC).convert("L").crop(box)
    if enh:
        im = ImageOps.autocontrast(im, cutoff=1)
    im = im.resize((int((x1 - x0) * s), int((y1 - y0) * s)), Image.NEAREST).convert("RGB")
    d = ImageDraw.Draw(im)
    gx = (x0 // step + 1) * step
    while gx < x1:
        X = (gx - x0) * s
        d.line([(X, 0), (X, im.size[1])], fill=(0, 160, 255), width=1)
        d.text((X + 2, 2), str(gx), fill=(0, 0, 255), font=f)
        gx += step
    gy = (y0 // step + 1) * step
    while gy < y1:
        Y = (gy - y0) * s
        d.line([(0, Y), (im.size[0], Y)], fill=(255, 120, 0), width=1)
        d.text((2, Y + 2), str(gy), fill=(200, 60, 0), font=f)
        gy += step
    return im


def main():
    out, s, step = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
    enh = "--enh" in sys.argv
    boxes = [tuple(int(v) for v in b.split(",")) for b in sys.argv[4:] if not b.startswith("--")]
    try:
        f = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        f = ImageFont.load_default()
    ims = [tile(b, s, step, enh, f) for b in boxes]
    W = sum(i.size[0] for i in ims) + 6 * (len(ims) - 1)
    H = max(i.size[1] for i in ims)
    canvas = Image.new("RGB", (W, H), (255, 0, 255))
    x = 0
    for i in ims:
        canvas.paste(i, (x, 0))
        x += i.size[0] + 6
    canvas.save(out)
    print(out, canvas.size)


if __name__ == "__main__":
    main()
