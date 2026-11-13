"""Which hull stations form the IMG_9391 left outline per row band (zc5 camera)?"""
import sys, json, importlib
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from hr26 import params as P, curves as C
UPY = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/undervann/py"
sys.path.insert(1, UPY)
import numpy as np
import common as c, uwlib as U
import photos as PH
cam = U.Cam(json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"][:7], 1500, 2000)
s0p = {}; exec(open(sys.argv[2] + "/hr26/params.py", encoding="utf-8").read(), s0p)
DW_AFT = [(5600.0, 0.0), (5900.0, 0.0), (6800.0, 100.0), (7400.0, 170.0), (7800.0, 210.0), (8000.0, 210.0)]
B4 = dict(SECTION_N=list(P.SECTION_N), SECTION_DEADRISE=list(P.SECTION_DEADRISE), DEADWOOD_H=list(P.DEADWOOD_H), DEADWOOD_W=P.DEADWOOD_W, CANOE_BOTTOM_HIDDEN=list(P.CANOE_BOTTOM_HIDDEN))
VAR = {"HEAD": dict(SECTION_N=s0p["SECTION_N"], SECTION_DEADRISE=s0p["SECTION_DEADRISE"], DEADWOOD_H=[(0.0, 0.0), (8000.0, 0.0)], DEADWOOD_W=180.0, CANOE_BOTTOM_HIDDEN=s0p["CANOE_BOTTOM_HIDDEN"]),
       "V1": dict(),
       "C1": dict(SECTION_DEADRISE=[(0.00, 45.0), (0.127, 15.0), (0.20, 4.0), (0.30, 2.0), (0.62, 2.0), (0.70, 12.0), (0.78, 24.0), (0.90, 15.0), (1.00, 3.0)],
                  SECTION_N=[(0.00, 2.4), (0.15, 3.1), (0.35, 3.4), (0.60, 3.5), (0.80, 4.2), (1.00, 4.2)], DEADWOOD_H=DW_AFT, DEADWOOD_W=[(5900.0, 200.0), (6800.0, 120.0)])}
for name, kw in VAR.items():
    for k, v in {**B4, **kw}.items(): setattr(P, k, v)
    C = importlib.reload(sys.modules["hr26.curves"]); c.C = C; U.c.C = C
    V, F = PH.mesh()
    u, v, zc = cam.project(V)
    ok = zc > 150
    out = []
    for r in (780, 820, 860, 900, 930):
        m = ok & (np.abs(v - r) < 1.5) & (V[:, 1] < 0)
        if not m.any(): continue
        i = np.where(m)[0][np.argmin(u[m])]
        obs = float(np.interp(r, PH.L91[:, 0], PH.L91[:, 1]))
        out.append(f"row {r}: x {V[i,0]:.0f} y {V[i,1]:.0f} z {V[i,2]:.0f} (model u {u[i]:.0f}, photo {obs:.0f})")
    print(name, " | ".join(out), flush=True)
