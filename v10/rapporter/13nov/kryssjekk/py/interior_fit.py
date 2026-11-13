"""Hull half-breadth at the interior's key heights (outer surface; model inner
surface = outer minus wall+margin is computed by curves.section_inner when it
exists), per stage. Compares with the interior spec: sole -285 between the
settee fronts (+-415), WC floor -212, seat top +195, backrest ref +435.

usage: python interior_fit.py <stage_dir> <tag>
"""
import sys, json
STAGE, TAG = sys.argv[1], sys.argv[2]
sys.path.insert(0, STAGE)
import numpy as np
from hr26 import params as P, curves as C


def hb_at(sec, z):
    """outer half-breadth at height z (first crossing from the keel up)."""
    s = np.asarray(sec, float)
    for i in range(len(s) - 1):
        z0, z1 = s[i, 1], s[i + 1, 1]
        if (z0 - z) * (z1 - z) <= 0 and z1 != z0:
            t = (z - z0) / (z1 - z0)
            return float(s[i, 0] + t * (s[i + 1, 0] - s[i, 0]))
    return float("nan")


has_inner = hasattr(C, "section_inner")
wall = P.HULL_WALL + getattr(P, "VOID_MARGIN", 0.0)
rows = []
for x in (2900, 3100, 3300, 3500, 3700, 3900, 4100, 4300, 4500, 4700, 4900, 5100, 5300, 5500):
    sec = C.section(float(x), 200)
    r = {"x": x, "bz": round(float(C.bottom_z(float(x))), 0)}
    for z in (-285, -212, -150, 0, 195, 435):
        r[f"o{z}"] = round(hb_at(sec, z), 0)
    if has_inner:
        try:
            si = C.section_inner(float(x), wall, 200)
            for z in (-285, -212, 0, 195):
                r[f"i{z}"] = round(hb_at(si, z), 0)
        except Exception as e:  # noqa
            r["inner_err"] = str(e)[:60]
    rows.append(r)
print(TAG, "wall+margin", wall, "has section_inner", has_inner)
keys = ["x", "bz", "o-285", "o-212", "o-150", "o0", "o195", "o435", "i-285", "i-212", "i0", "i195"]
print(" ".join(f"{k:>7s}" for k in keys))
for r in rows:
    print(" ".join(f"{r.get(k, float('nan')):7.0f}" for k in keys))
json.dump(rows, open(r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/out/interior_fit_%s.json" % TAG, "w"), indent=1)
