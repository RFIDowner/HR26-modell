"""Maaler planens ytterkontur (den tykke dekkslinjen) kolonne for kolonne."""
import sys
import numpy as np
from PIL import Image

im = np.asarray(Image.open(sys.argv[1]).convert("L"), dtype=float)
dark = im < 110
for x in range(380, 2250, 50):
    col = dark[980:1722, x - 1:x + 2].any(axis=1)
    ys = np.nonzero(col)[0] + 980
    if len(ys) == 0:
        print(x, "-")
        continue
    # foerste og siste moerke piksel = ytterkant oppe og nede
    top, bot = ys[0], ys[-1]
    # tykkelse paa linjen oppe/nede
    t_end = top
    while t_end + 1 < 1722 and dark[t_end + 1, x]:
        t_end += 1
    b_st = bot
    while b_st - 1 > 980 and dark[b_st - 1, x]:
        b_st -= 1
    print(x, "top %d-%d" % (top, t_end), "bot %d-%d" % (b_st, bot), "mid %.1f" % (0.5 * (top + bot)), "w %d" % (bot - top))
