"""kk_: 448-5-linjene i akterpartiet mot modellen (karmtopp, dekkskant, liste)."""
import json
import numpy as np
import common as c
import geo9374 as G
G.use_model(None)
from hr26 import deckhouse as D
P, C = c.P, c.C
J = c.ELINES
print("plan keys:", list(J["plan"].keys()))
ct = np.asarray(J["profile"]["coaming_top"]["xz"], float)
ct = ct[np.argsort(ct[:, 0])]
sl = np.asarray(J["profile"]["strake_line"]["xz"], float)
ad = np.asarray(J["profile"]["aft_dashed_345"]["xz"], float)
print(" x     448ct  448ct-30  model_ct  sheer   strake  | ct-sheer(448-30)")
for x in range(5700, 7951, 100):
    s = np.abs(ct[:, 0] - x) < 25
    z448 = np.median(ct[s, 1]) if s.any() else np.nan
    mct = D.coaming_top_z(x) if x < P.COAMING_X1 else np.nan
    print("%5d %7.0f %7.0f %8.0f %7.0f %7.0f | %5.0f" % (x, z448, z448 - 30, mct, C.sheer_z(x), C.strake_z(x), z448 - 30 - C.sheer_z(x)))
print("coaming_top ends:", ct[:3].round(1).tolist(), ct[-3:].round(1).tolist())
for k, v in J["plan"].items():
    a = np.asarray(v.get("x_halfbreadth", v.get("xy", [])), float)
    if a.size:
        print(k, v.get("what"), a.shape, a[:, 0].min().round(), a[:, 0].max().round())
