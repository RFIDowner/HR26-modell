"""Prototype: hjoernet mellom skrogside og akterspeil per hoyde, fra kurve-API-et."""
import sys, math, time
import numpy as np
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/stern"
sys.path.insert(0, WT)
from hr26 import curves as C, params as P

def side_y(x, z):
    sec = np.asarray(C.section(x, 60), float)
    zz = np.maximum.accumulate(sec[:, 1])
    if z <= zz[0]: return 0.0
    if z >= zz[-1]: return float(sec[-1, 0])
    return float(np.interp(z, zz, sec[:, 0]))

def psi_side(x, z, h=25.0):
    dy = (side_y(x - h, z) - side_y(x + h, z)) / (2 * h)
    return math.atan2(dy, -1.0)

def psi_tr(y):
    R = P.TRANSOM_CAMBER_R; k = math.sqrt(1 + P.TRANSOM_RAKE ** 2)
    return math.atan2(1.0, -k * y / math.sqrt(R * R - y * y))

def corner_K(z):
    if side_y(C.transom_x(z, 0.0), z) <= 1.0: return None
    lo, hi = 0.0, 1500.0
    for _ in range(45):
        m = 0.5 * (lo + hi)
        if side_y(C.transom_x(z, m), z) > m: lo = m
        else: hi = m
    y = 0.5 * (lo + hi)
    return C.transom_x(z, y), y

t = time.time()
for z in np.arange(-260, 1001, 50):
    K = corner_K(z)
    if K is None: print(f"z={z:6.0f} no hull at transom"); continue
    th = math.degrees(psi_side(K[0] - 1, z) - psi_tr(K[1]))
    print(f"z={z:6.0f} K=({K[0]:7.1f},{K[1]:6.1f}) side psi={math.degrees(psi_side(K[0]-1,z)):6.1f} transom psi={math.degrees(psi_tr(K[1])):6.1f} theta={th:5.1f}  sheer(Kx)={C.sheer_z(K[0]):.0f}")
print("tid", time.time() - t)
