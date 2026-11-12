"""Sammenligner planens ytterkontur med modellens dekkslinje."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "snap"))
import numpy as np
from PIL import Image
from hr26 import curves as C

im = np.asarray(Image.open(sys.argv[1]).convert("L"), dtype=float)
S, BOW, CL = 4.256, 2241.0, 1333.3
dark = im < 110
rows = []
for px in range(420, 2230, 60):
    col = dark[990:1722, px - 1:px + 2].any(axis=1)
    ys = np.nonzero(col)[0] + 990
    top0 = ys[0]
    t1 = top0
    while dark[t1 + 1, px]:
        t1 += 1
    bot1 = ys[-1]
    b0 = bot1
    while dark[b0 - 1, px]:
        b0 -= 1
    yt = 0.5 * (top0 + t1)
    yb = 0.5 * (b0 + bot1)
    x = (BOW - px) * S
    hb = C.deck_half_breadth(x)
    rows.append((px, x, (CL - yt) * S, (yb - CL) * S, hb))
    print("px %4d x %6.0f  port %6.0f  stb %6.0f  mean %6.0f  model %6.0f  diff %5.0f  ratio %.3f" % (
        px, x, (CL - yt) * S, (yb - CL) * S, 0.5 * (yb - yt) * S, hb, 0.5 * (yb - yt) * S - hb, 0.5 * (yb - yt) * S / hb))
