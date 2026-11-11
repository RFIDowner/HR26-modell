import sys, math
import numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface")
from common import *
sys.path.insert(0, REPO)
from hr26 import curves as C, params as P, hull as H
D = np.load(OUT + "/a1.npz")
Vf, F, fn, cls, E, f1, f2, dih, area = (D[k] for k in ("Vf", "F", "fn", "cls", "E", "f1", "f2", "dih", "area"))
c = Vf[F].mean(1)
# strake path stations exactly as rubbing_strake() makes them (starboard)
path = H._strake_path(48)
px = np.array([p[0][0] for p in path]); py = np.array([p[0][1] for p in path]); pz = np.array([p[0][2] for p in path])
side_x = px[:-12]
print("strake path: side stations", len(side_x), " spacing min/median/max", np.diff(side_x).min().round(1), np.median(np.diff(side_x)).round(1), np.diff(side_x).max().round(1))
# heading of the strake centre line between path points (plan view) and its change per path point
hd = np.degrees(np.arctan2(np.diff(py), np.diff(px)))
turn = np.abs(np.diff(hd))
pitch = np.degrees(np.arctan2(np.diff(pz), np.hypot(np.diff(px), np.diff(py))))
dpitch = np.abs(np.diff(pitch))
print("plan-view kink at each side path point (deg): median %.2f, p90 %.2f, max %.2f" % (np.median(turn[:len(side_x) - 2]), np.percentile(turn[:len(side_x) - 2], 90), turn[:len(side_x) - 2].max()))
print("profile (sheer) kink at each side path point (deg): median %.3f, max %.3f" % (np.median(dpitch[:len(side_x) - 2]), dpitch[:len(side_x) - 2].max()))
for i in range(0, len(side_x) - 2, 4):
    print(f"   x {side_x[i+1]:7.0f}: segment {side_x[i+1]-side_x[i]:6.0f} mm, plan kink {turn[i]:.2f} deg, sheer kink {dpitch[i]:.3f} deg")
print("around the transom corner (last side pt + 12 transom pts): plan kinks", np.round(turn[len(side_x) - 3:], 1))
# measured in the STL: outer vertical face of the strake on starboard
outer = (cls == 2) & (np.abs(fn[:, 2]) < 0.5) & (c[:, 1] * fn[:, 1] > 0) & (c[:, 1] > 0)
e2 = outer[f1] & outer[f2]
kink = e2 & (dih > 0.05)
mx = 0.5 * (Vf[E[:, 0], 0] + Vf[E[:, 1], 0])
dx = np.abs(Vf[E[:, 0], 0] - Vf[E[:, 1], 0])
print(f"\nSTL: strake outer-face triangles (stb) {outer.sum()}, interior edges {e2.sum()}, with dihedral > 0.05 deg: {kink.sum()}")
near = np.min(np.abs(mx[:, None] - side_x[None, :]), axis=1)
k1 = kink & (near < 2) & (dx < 3)
print(f"   creases lying on strake path stations (|dx|<3 mm): {k1.sum()}; dihedral median {np.median(dih[k1]):.2f}, max {dih[k1].max():.2f}")
k2 = kink & ~k1
print(f"   other creases (diagonals of twisted ruled panels etc.): {k2.sum()}; dihedral median {np.median(dih[k2]):.3f}, p90 {np.percentile(dih[k2],90):.3f}")
for x0 in (300, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 7600):
    m = k1 & (np.abs(mx - x0) < 400)
    if m.sum():
        print(f"   near x={x0}: station creases {m.sum()}, dihedral {np.round(np.sort(dih[m])[-3:], 2)}")
np.savez(OUT + "/strake.npz", side_x=side_x, turn=turn, dpitch=dpitch)
