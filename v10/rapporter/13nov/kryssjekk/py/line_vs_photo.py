"""(1) where does the canoe-body centreline reach the level of the 448-5 dash-dot
outline (it closes across the centreline at x ~2280)? (2) project the traced
dash-dot points at z=-300 into IMG_9391 with the zc5 camera and compare with
the photo's red underwater outline in the same rows."""
import sys, json
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from hr26 import params as P, curves as C
UPY = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/undervann/py"
KK = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/"
sys.path.insert(1, UPY)
import numpy as np
import common as c, uwlib as U
import photos as PH
for x in (2100, 2200, 2250, 2280, 2300, 2350, 2400, 2500):
    print("x %d bottom_z %.0f" % (x, C.bottom_z(float(x))))
el = c.ELINES["profile"]
for name in ("hull_fwd_bottom",):
    a = np.asarray(el[name]["xz"], float)
    for x in (2100, 2200, 2280, 2400):
        if a[:, 0].min() <= x <= a[:, 0].max():
            zE = float(np.interp(x, a[:, 0], a[:, 1])); print("Enderlein %s x %d: z_E %.0f -> model %.0f" % (name, x, zE, (zE - 25.5) / 0.968))
cam = U.Cam(json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"][:7], 1500, 2000)
tr = json.load(open(KK + "out/dashdot_trace.json"))
ro = np.array(json.load(open(c.W + "/out/t9391.json"))["red_outline"])   # row, uL, uR
for zl in (-285.0, -300.0, -320.0):
    out = []
    for side, sgn in (("stb", 1), ("port", -1)):
        a = np.array(tr[side]); a = a[(a[:, 0] >= 3700) & (a[:, 0] <= 5300)]
        X = np.c_[a[:, 0], sgn * np.abs(a[:, 1]), np.full(len(a), zl)]
        u, v, _ = cam.project(X)
        for xi, ui, vi in zip(a[:, 0], u, v):
            if ro[:, 0].min() <= vi <= ro[:, 0].max():
                uL = float(np.interp(vi, ro[:, 0], ro[:, 1])); uR = float(np.interp(vi, ro[:, 0], ro[:, 2]))
                # outside the photo outline by (px): left of uL or right of uR
                out.append((xi, vi, max(uL - ui, ui - uR)))
    o = np.array(out)
    print("z %.0f: %d points in rows %.0f-%.0f; outside the photo outline by median %+.0f px (max %+.0f); x of worst %.0f"
          % (zl, len(o), o[:, 1].min(), o[:, 1].max(), np.median(o[:, 2]), o[:, 2].max(), o[np.argmax(o[:, 2]), 0]))
