"""Glatt akterdel av WATERPLANE: kubisk B-spline med V9-punktene som kontrollpolygon
(kutter hjoernene, ligger aldri utenfor V9), samplet paa tabellens t."""
import sys, os
import numpy as np
sys.path.insert(0, "origpkg")
from hr26o import params as P0
import fit_lib as L
wp = np.array(P0.WATERPLANE)
ctrl = wp[wp[:, 0] >= 0.65]
n = len(ctrl)
t = np.r_[[0.0] * 4, np.linspace(0, 1, n - 2)[1:-1], [1.0] * 4]
u = np.linspace(0, 1, 20001)
B = L.basis(u, t)
X, Y = B @ ctrl[:, 0], B @ ctrl[:, 1]
def poly(tt):
    return np.interp(tt, wp[:, 0], wp[:, 1])
print("maks (kurve - V9-polygon):", (Y - poly(X)).max().round(4))
for tq in [0.75, 0.80, 0.85, 0.90, 0.93, 0.95, 0.97, 0.99, 1.00, 1.015]:
    print(f"  t={tq:.3f}: V9 {poly(tq):.3f}  glatt {np.interp(tq, X, Y):.3f}")
