import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-edges")
from vlib import *
F = np.load("ours_full.npy")
S = plane_section(F, 1, 0.5)[:, :, [0,2]]
# vertical segments at x~170 (block front) and x~2200 (coach front)
for xv in (170.0, 2200.0, 690.0):
    m = (np.abs(S[:,0,0]-xv)<1.5)&(np.abs(S[:,1,0]-xv)<1.5)
    zz = np.sort(S[m][:,:,1].ravel())
    if len(zz): print(f"segments on x~{xv}: z from {zz.min():.1f} to {zz.max():.1f}, n={m.sum()}")
# block bottom: horizontal segment near z~793
m = (np.abs(S[:,0,1]-S[:,1,1])<0.5)&(S[:,:,0].max(1)<700)&(S[:,:,1].mean(1)<900)&(S[:,:,1].mean(1)>700)
for s in S[m]: print("horizontal seg (bottom of block?)", np.round(s,1).tolist())
# stem: analytic
import math
def x_stem(z, top=1204.0):  # approximately; sheer_z(0) from code below
    return 1008.0*(1.0-(z/top)**(1/1.3))
sys.path.insert(0, VDIR + "/repo")
from hr26 import curves as C
top = C.sheer_z(0.0)
print("sheer_z(0)=", top, " deck_z(430,0)=", C.deck_z(430,0.0), " block z range", C.deck_z(430,0.0)-420, C.deck_z(430,0.0)+140)
for z in (793, 800, 850, 900, 947, 1000, 1100):
    # find stem x in the STL section: min x of boundary among segments crossing this z, excluding the block front x=170
    cr = (S[:,:,1].min(1) <= z) & (S[:,:,1].max(1) >= z)
    xs = []
    for s in S[cr]:
        (x0,z0),(x1,z1) = s
        if abs(z1-z0) < 1e-9: continue
        xs.append(x0 + (z-z0)*(x1-x0)/(z1-z0))
    xs = np.sort(np.array(xs))
    print(f" z={z}: analytic stem x={1008*(1-(z/top)**(1/1.3)):.1f}; STL boundary x={np.round(xs[:6],1)}")
