import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
T0 = load(OURS)
for a in (44.0, 45.0, 46.0):
    T = rotz(T0, -a); V = T.reshape(-1,3)
    T[:, :, 1] -= 0.5 * (V[:, 1].max() + V[:, 1].min()); T[:, :, 0] -= V[:, 0].min()
    T *= 30; T[:, :, 0] += 4.0; T[:, :, 2] -= 1400
    seg = section(T, 2, 1300.0)[:, :, [0, 1]]
    lines = chain(seg)
    out = []
    for L in lines:
        x0, x1 = L[:, 0].min(), L[:, 0].max(); y0, y1 = L[:, 1].min(), L[:, 1].max()
        if x1 - x0 < 600: out.append(f"x {0.5*(x0+x1):6.0f} y {0.5*(y0+y1):6.0f} ({x1-x0:4.0f}x{y1-y0:4.0f})")
    print(a, " | ".join(out))
