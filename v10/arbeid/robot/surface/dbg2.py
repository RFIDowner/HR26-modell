import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface")
from common import *
T32 = load_raw(OURS)
V0, F = weld(T32)
for a in (43.0, 44.0, 45.0):
    V = rotz(V0, -a)
    zb = (V[:, 2] > 15) & (V[:, 2] < 70)
    xs = np.linspace(V[:, 0].min() + 20, V[:, 0].max() - 20, 12)
    mids = []
    for x in xs:
        m = zb & (np.abs(V[:, 0] - x) < 1.0)
        mids.append(0.5 * (V[m, 1].max() + V[m, 1].min()))
    mids = np.array(mids)
    p = np.polyfit(xs, mids, 1)
    print(a, "centre-line slope", p[0], "-> residual angle deg", np.degrees(np.arctan(p[0])), "spread", np.ptp(mids - np.polyval(p, xs)))
