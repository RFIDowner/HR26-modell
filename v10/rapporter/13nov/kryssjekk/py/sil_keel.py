"""IMG_9391 (astern, undervann zc5 camera) underwater-outline residuals per row
band, hull alone (as the undervann fits did) and hull + keel (CAD keel
tessellated into the same mesh). Positive = model wider than the photo.

usage: python sil_keel.py <stage_dir> <tag>
"""
import sys, json
sys.dont_write_bytecode = True
STAGE, TAG = sys.argv[1], sys.argv[2]
sys.path.insert(0, STAGE)
from hr26 import params as P, curves as C, appendages as AP
UPY = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/undervann/py"
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/out"
sys.path.insert(1, UPY)
import numpy as np
import common as c, uwlib as U
assert c.C is C
import photos as PH

V, F = PH.mesh()
k = AP.keel().val()
vs, tris = k.tessellate(2.0, 0.3)
KV = np.array([(v.x, v.y, v.z) for v in vs], float)
KF = np.array(tris, int) + len(V)
V2 = np.vstack([V, KV]); F2 = np.vstack([F, KF])

res = {}
for name, (VV, FF) in (("hull", (V, F)), ("hull+keel", (V2, F2))):
    a, b = PH.e9391(VV, FF)
    row = {}
    for side, arr, rows in (("L", a, PH.L91[:, 0]), ("R", b, PH.R91[:, 0])):
        for r0, r1 in ((755, 800), (800, 870), (870, 945)):
            m = (rows >= r0) & (rows < r1)
            if m.any():
                row[f"{side}{r0}-{r1}"] = round(float(np.mean(arr[m])), 1)
        row[f"{side}_rms"] = round(float(np.sqrt(np.mean(arr ** 2))), 1)
        row[f"{side}_mean"] = round(float(np.mean(arr)), 1)
    res[name] = row
    print(TAG, f"{name:10s}", row, flush=True)
# where does the keel change the outline? rows with |difference| > 2 px
a1, b1 = PH.e9391(V, F); a2, b2 = PH.e9391(V2, F2)
dL = a2 - a1; dR = b2 - b1
chg = [(int(r), round(float(d), 1)) for r, d in zip(PH.L91[:, 0], dL) if abs(d) > 2]
chgR = [(int(r), round(float(d), 1)) for r, d in zip(PH.R91[:, 0], dR) if abs(d) > 2]
print(TAG, "rows where the keel widens the LEFT outline by >2 px:", chg[:3], "...", chg[-3:], "n", len(chg))
print(TAG, "rows where the keel widens the RIGHT outline by >2 px:", chgR[:3], "...", chgR[-3:], "n", len(chgR))
res["keel_rows_L"] = chg; res["keel_rows_R"] = chgR
json.dump(res, open(OUT + f"/sil_keel_{TAG}.json", "w"), indent=1)
