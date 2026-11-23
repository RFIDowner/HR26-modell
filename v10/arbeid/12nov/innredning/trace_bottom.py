"""Sporer skrogets ytre bunnlinje (forfoten) i profilen: laveste moerke
piksel per kolonne mellom gitte rader. Skriver px, py."""
import sys
import numpy as np
from PIL import Image

im = np.asarray(Image.open(sys.argv[1]).convert("L"), dtype=float)
x0, x1, y0, y1 = [int(v) for v in sys.argv[2:6]]
dark = im < 150
for x in range(x0, x1, 10):
    col = dark[y0:y1, x - 1:x + 2].sum(axis=1) >= 2
    ys = np.nonzero(col)[0]
    # hopp over brettekanten (683-696)
    ys = [y + y0 for y in ys if not (683 <= y + y0 <= 697)]
    if ys:
        print(x, max(ys))
