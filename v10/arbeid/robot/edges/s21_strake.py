import sys, math
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges/repo")
import numpy as np
from hr26 import hull as H, params as P, curves as C
path = H._strake_path(48)
pts = np.array([p for p, _ in path])
print("strake path points (stb):", len(pts), " first x", pts[0, 0], " side->transom corner at x", round(pts[-13, 0], 1), "y", round(pts[-13, 1], 1), "z", round(pts[-13, 2], 1))
d = np.diff(pts, axis=0)
L = np.linalg.norm(d, axis=1)
# plan-view heading and kink between consecutive segments
hd = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
k = np.diff(hd); k = (k + 180) % 360 - 180
pr = np.degrees(np.arctan2(d[:, 2], np.hypot(d[:, 0], d[:, 1])))
kp = np.diff(pr)
print(" seg  x_from  x_to   len    plan-kink  profile-kink (deg)")
for i in range(len(d) - 1):
    if i < 6 or i > len(d) - 16 or i % 8 == 0:
        print(f" {i:3d} {pts[i,0]:7.0f} {pts[i+1,0]:7.0f} {L[i]:6.0f}   {k[i]:7.2f}   {kp[i]:7.2f}")
side = slice(0, len(d) - 13)
print("max plan kink along side (excluding transom corner): %.2f deg; median %.2f; at bow segs 0-5:" % (np.abs(k[:len(d)-14]).max(), np.median(np.abs(k[:len(d)-14]))), np.round(k[:6], 2))
print("kink at the side->transom corner: %.1f deg" % k[len(d) - 14:len(d) - 11].sum())
# sagitta of a straight 300 mm segment on the strake's plan curve: max deviation between chord and spline
