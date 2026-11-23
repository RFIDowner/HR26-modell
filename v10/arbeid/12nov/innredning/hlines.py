"""Finner lange vannrette linjer: antall moerke piksler per rad i et x-intervall."""
import sys
import numpy as np
from PIL import Image

im = np.asarray(Image.open(sys.argv[1]).convert("L"), dtype=float)
x0, x1, y0, y1 = [int(v) for v in sys.argv[2:6]]
thr = float(sys.argv[6]) if len(sys.argv) > 6 else 150
dark = im[y0:y1, x0:x1] < thr
cnt = dark.sum(axis=1)
for i, c in enumerate(cnt):
    if c > 0.25 * (x1 - x0):
        print(y0 + i, int(c))
