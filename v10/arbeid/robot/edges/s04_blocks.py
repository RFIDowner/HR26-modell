import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *

T = np.load(OUT + "/ours_full.npy")
# plan section through the top of the deck fittings
for zf in (1300.0, 1250.0):
    seg = section(T, 2, zf)[:, :, [0, 1]]
    lines = chain(seg, tol=1e-3)
    print(f"--- plan section z={zf}: {len(lines)} loops")
    for L in lines:
        x0, x1 = L[:, 0].min(), L[:, 0].max(); y0, y1 = L[:, 1].min(), L[:, 1].max()
        print(f"  loop n={len(L):5d}  x {x0:7.0f}..{x1:7.0f} ({x1-x0:5.0f})  y {y0:7.0f}..{y1:7.0f} ({y1-y0:5.0f})")
# cleats and winch tops
V = T.reshape(-1, 3)
for xc in (700, 4900, 7500):
    sel = V[(np.abs(V[:, 0] - xc) < 200) & (V[:, 1] > 0) & (V[:, 1] > 500)]
    print("cleat region x", xc, "max z", sel[:, 2].max().round(1))
