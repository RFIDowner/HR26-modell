"""Loddrette linjer: kolonner med mange moerke piksler i et y-intervall.
Skriver sammenhengende loep (y-fra, y-til) for kolonner over terskelen."""
import sys
import numpy as np
from PIL import Image

im = np.asarray(Image.open(sys.argv[1]).convert("L"), dtype=float)
x0, x1, y0, y1 = [int(v) for v in sys.argv[2:6]]
minrun = int(sys.argv[6]) if len(sys.argv) > 6 else 40
thr = 140
dark = im < thr
for x in range(x0, x1):
    col = dark[y0:y1, x]
    # lengste loep med smaa hull (<=3 px)
    runs = []
    start, gap = None, 0
    for i, v in enumerate(col):
        if v:
            if start is None:
                start = i
            gap = 0
            end = i
        else:
            if start is not None:
                gap += 1
                if gap > 3:
                    runs.append((start, end))
                    start, gap = None, 0
    if start is not None:
        runs.append((start, end))
    long = [(a + y0, b + y0) for a, b in runs if b - a >= minrun]
    if long:
        print(x, long)
