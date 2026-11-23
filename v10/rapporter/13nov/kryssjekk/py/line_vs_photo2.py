import sys, json
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from hr26 import params as P, curves as C
UPY = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/undervann/py"
KK = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/"
sys.path.insert(1, UPY)
import numpy as np
import common as c, uwlib as U
cam = U.Cam(json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"][:7], 1500, 2000)
tr = json.load(open(KK + "out/dashdot_trace.json"))
ro = np.array(json.load(open(c.W + "/out/t9391.json"))["red_outline"])
for zl in (-300.0,):
    for side, sgn in (("stb", 1), ("port", -1)):
        a = np.array(tr[side]); a = a[(a[:, 0] >= 3700) & (a[:, 0] <= 5300)]
        X = np.c_[a[:, 0], sgn * np.abs(a[:, 1]), np.full(len(a), zl)]
        u, v, _ = cam.project(X)
        uL = np.interp(v, ro[:, 0], ro[:, 1]); uR = np.interp(v, ro[:, 0], ro[:, 2])
        outside = np.where(u < 0.5 * (uL + uR), uL - u, u - uR)
        print("z %.0f %s (y %s): rows %.0f-%.0f, u %.0f-%.0f, outside outline by median %+.0f px (range %+.0f..%+.0f)"
              % (zl, side, "+" if sgn > 0 else "-", v.min(), v.max(), u.min(), u.max(), np.median(outside), outside.min(), outside.max()))
# the mirrored midline of the photo outline vs the camera's centreline projection at those rows
for r in (860, 880, 900):
    uL = np.interp(r, ro[:, 0], ro[:, 1]); uR = np.interp(r, ro[:, 0], ro[:, 2])
    print("row %d: photo outline %.0f..%.0f (mid %.0f)" % (r, uL, uR, 0.5 * (uL + uR)))
X = np.array([[x, 0.0, -300.0] for x in (3700, 4500, 5300)]); u, v, _ = cam.project(X)
print("centreline points at z -300 project to u", [round(float(t)) for t in u], "rows", [round(float(t)) for t in v])
