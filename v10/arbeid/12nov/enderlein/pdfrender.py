"""Render PDF pages to PNG (work/), e.g. the brochure page with the 1:50 drawings.

usage: python -I pdfrender.py file.pdf page(1-based) dpi out.png [clip x0,y0,x1,y1 in pt]
"""
import os
import sys

import pymupdf as fitz

SRC = os.path.join(os.path.expanduser("~"), "Documents", "Seilbåt", "Hallberg-Rassy-kilder")

fn, page, dpi, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
d = fitz.open(os.path.join(SRC, fn))
p = d[page - 1]
print("page size pt", p.rect)
clip = None
if len(sys.argv) > 5:
    clip = fitz.Rect(*[float(v) for v in sys.argv[5].split(",")])
pix = p.get_pixmap(dpi=dpi, clip=clip)
pix.save(out)
print(out, pix.width, pix.height)
for img in p.get_images(full=True):
    print("embedded image", img[:4])
