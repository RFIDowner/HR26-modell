"""Evaluate model from repo path argv[1]: photo metrics, hydro, topside change vs snap_before, cradle/transom numbers."""
import sys, os, json
sys.path.insert(0, sys.argv[1])
from hr26 import params as P, curves as C
sys.path.insert(1, '.')
import numpy as np
import common as c, uwlib as U, photos as PH
tag = sys.argv[2]
V, F = PH.mesh()
r = PH.summary(tag, V, F)
before = json.load(open(c.W + "/out/snap_before.json"))
worst, where = 0.0, None
for xs, p0 in before["top"].items():
    p0 = np.array(p0); zs = before["strake"][xs]
    p0 = p0[p0[:, 1] >= zs - 30]
    p = np.array(C.section(float(xs), 400))
    y = np.interp(p0[:, 1], p[:, 1], p[:, 0])
    d = np.max(np.abs(y - p0[:, 0]))
    if d > worst:
        worst, where = d, xs
print(f"  max change at/above the strake (strake-30 mm up): {worst:.2f} mm at x {where}")
for x in P.STAND_STATIONS:
    s = np.array(C.section(x, 300))
    print(f"  cradle x {x}: bottom {C.bottom_z(x):.0f}, half-breadth at z -300/-200/-100/0: " +
          "/".join(f"{np.interp(z, s[:, 1], s[:, 0]):.0f}" for z in (-300, -200, -100, 0)))
xt = U.transom_x(-200, 0)
s = np.array(C.section(7790.0, 300))
print("  section at 7790: half-breadth at z -400/-350/-300/-250/-200/-150/-100/0:",
      "/".join(f"{np.interp(z, s[:, 1], s[:, 0]):.0f}" for z in (-400, -350, -300, -250, -200, -150, -100, 0)), " foot", round(C.bottom_z(7790.0)))
for z in P.RUDDER_PIN_Z:
    x_t = U.transom_x(z, 0.0)
    xs = x_t - P.RUDDER_PIN_L
    sec = np.array(C.section(xs, 300))
    print(f"  rudder pin z {z}: transom x {x_t:.0f}, pin inner end x {xs:.0f}: hull bottom on CL {C.bottom_z(xs):.0f}, "
          f"half-breadth at pin z {np.interp(z, sec[:, 1], sec[:, 0]):.0f} (pin radius {P.RUDDER_PIN_D/2:.0f})")
c.save_json(dict(e91=r["e91"], e88=r["e88"], h=r["h"]), c.W + f"/out/eval_{tag}.json")
