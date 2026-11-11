import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from corner import densify
T = np.load(OUT + "/ours_full.npy")
V = T.reshape(-1, 3)
def bbox(sel_fn, name):
    m = sel_fn(V)
    S = V[m]
    print(f"{name:28s} x {S[:,0].min():7.0f}..{S[:,0].max():7.0f}  y {S[:,1].min():7.0f}..{S[:,1].max():7.0f}  z {S[:,2].min():6.0f}..{S[:,2].max():6.0f}")
# cleats: above deck near the edges
bbox(lambda V: (V[:,0] > 500) & (V[:,0] < 900) & (V[:,1] > 120) & (V[:,1] < 340) & (V[:,2] > 1225), "cleat x700 stb (above deck)")
bbox(lambda V: (V[:,0] > 4700) & (V[:,0] < 5100) & (V[:,1] > 1000) & (V[:,2] > 1110), "cleat x4900 stb (above deck)")
bbox(lambda V: (V[:,0] > 7300) & (V[:,0] < 7700) & (V[:,1] > 600) & (V[:,2] > 1010), "cleat x7500 stb (above deck)")
bbox(lambda V: (V[:,0] > 5700) & (V[:,0] < 6100) & (V[:,1] > 600) & (V[:,1] < 1100) & (V[:,2] > 1170), "winch x5900 stb (above karm)")
bbox(lambda V: (V[:,0] > 100) & (V[:,0] < 760) & (np.abs(V[:,1]) < 120) & (V[:,2] > 1220), "anchor roller (above deck)")
# sprayhood centreline profile: section y=0 between 5000 and 6300, z>1360
s = section(T, 1, 0.0)[:, :, [0, 2]]
P = densify(s)
Q = P[(P[:, 0] > 5000) & (P[:, 0] < 6300) & (P[:, 1] > 1400)]
for z in (1450, 1550, 1650, 1700, 1740):
    r = Q[np.abs(Q[:, 1] - z) < 2]
    print(f" sprayhood y=0 z={z}: x min {r[:,0].min():.0f} max {r[:,0].max():.0f}")
# sprayhood width at x=5600
s = section(T, 0, 5600.0)[:, :, [1, 2]]
P = densify(s); Q = P[(P[:, 1] > 1400)]
print(" sprayhood x=5600: max |y| above z1400:", np.abs(Q[:, 0]).max().round(0), " top z", Q[:, 1].max().round(0))
for z in (1450, 1550, 1650, 1700):
    r = Q[np.abs(Q[:, 1] - z) < 2]
    print(f"   z={z}: half width {np.abs(r[:,0]).max():.0f}")
