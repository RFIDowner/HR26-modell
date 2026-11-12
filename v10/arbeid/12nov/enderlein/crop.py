"""Crop a region of the Enderlein drawing, upscale it and draw a pixel grid
with labels (original pixel coordinates), so features can be read off.

usage: python -I crop.py x0 y0 x1 y1 scale out.png [grid_step] [--enh]
"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

SRC = r"C:\Users\stig\Documents\Seilbåt\Hallberg-Rassy-kilder\HR26interior448-5.jpeg"


def main():
    x0, y0, x1, y1 = (int(v) for v in sys.argv[1:5])
    s = float(sys.argv[5])
    out = sys.argv[6]
    step = int(sys.argv[7]) if len(sys.argv) > 7 and not sys.argv[7].startswith("--") else 50
    enh = "--enh" in sys.argv
    im = Image.open(SRC).convert("L")
    c = im.crop((x0, y0, x1, y1))
    if enh:
        c = ImageOps.autocontrast(c, cutoff=1)
    c = c.resize((int((x1 - x0) * s), int((y1 - y0) * s)), Image.LANCZOS).convert("RGB")
    d = ImageDraw.Draw(c)
    try:
        f = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        f = ImageFont.load_default()
    gx = (x0 // step + 1) * step
    while gx < x1:
        X = (gx - x0) * s
        d.line([(X, 0), (X, c.size[1])], fill=(0, 160, 255) if gx % (step * 2) == 0 else (140, 200, 255), width=1)
        d.text((X + 2, 2), str(gx), fill=(0, 0, 255), font=f)
        gx += step
    gy = (y0 // step + 1) * step
    while gy < y1:
        Y = (gy - y0) * s
        d.line([(0, Y), (c.size[0], Y)], fill=(255, 120, 0) if gy % (step * 2) == 0 else (255, 190, 130), width=1)
        d.text((2, Y + 2), str(gy), fill=(200, 60, 0), font=f)
        gy += step
    c.save(out)
    print(out, c.size)


if __name__ == "__main__":
    main()
