"""List the lines crossed by vertical (or horizontal) scan lines: centre,
width and darkness of every dark run. Averages a few columns to reduce noise.

usage: python -I vprof.py v|h pos0,pos1,... from to [thr] [halfwidth]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from img import gray, centroid_runs

a = gray()
mode = sys.argv[1]
poss = [int(v) for v in sys.argv[2].split(",")]
lo, hi = int(sys.argv[3]), int(sys.argv[4])
thr = float(sys.argv[5]) if len(sys.argv) > 5 else 200
hw = int(sys.argv[6]) if len(sys.argv) > 6 else 1
for p in poss:
    if mode == "v":
        prof = a[lo:hi, p - hw:p + hw + 1].mean(axis=1)
    else:
        prof = a[p - hw:p + hw + 1, lo:hi].mean(axis=0)
    r = centroid_runs(prof, thr)
    print(f"{mode}{p}: " + "  ".join(f"{lo + c:.1f}({e - s + 1},{int(m)})" for c, s, e, m in r))
