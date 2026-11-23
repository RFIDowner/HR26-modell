"""Foelsomhet for IMG_9389-restene: (1) kameravariantene fra cam9389.py,
(2) enkle formendringer av dagens modell (bunnen dypere, bredere, flatere)
for aa vite hva bildet maaler. Kjoeres fra denne mappa:
  python ../../../../tools/memcap.py --gb 3 -- python vurder9389.py"""
import json
import sys

import numpy as np

import head9389  # noqa: F401  (HR26_REF=work for arbeidskopien)
import common as c
import uwlib as U
import e9389 as E
import photos

V, F = photos.mesh()
modes = json.load(open(c.W + "/out/cam9389_modes.json"))["modes"]
p0 = list(E.CAM.p); dz0 = E.DZR; k0 = E.KBT
out = {}
print("== kameravarianter ==")
print("modell:", head9389.REF, c.P.__file__)
for name, m in modes.items():
    q = m["q"]
    dzr = q[8] if len(q) > 8 else (0.0 if m.get("mode") == "bt38" else dz0)
    dzt = q[7] if len(q) > 8 else (0.0 if m.get("mode") == "bt38" else E.DZT)
    E.set_cam(m["p"], dzr, dzt, q[9] if len(q) > 9 else 0.0)
    rb, rf = E.parts(V, F)
    D = E._diag(V, F)
    xb = D["xb"][:, 0]
    bins = [(0, 1500), (1500, 2000), (2000, 2500), (2500, 3400)]
    row = {"front": float(rf.mean())}
    for a, b in bins:
        mm = (xb >= a) & (xb < b)
        row["%d-%d" % (a, b)] = float(rb[mm].mean()) if mm.any() else float("nan")
    rbt = E.resid_bt(V, F); ok = rbt != E.CAP
    row["bt"] = float(rbt[ok].mean()) if ok.any() else float("nan")
    row["mm"] = {"%d-%d" % (a, b): float((rb * D["mmb"])[(xb >= a) & (xb < b)].mean()) for a, b in bins}
    row["dzr"] = dzr
    out[name] = row
    print("%-18s front %+6.1f | bunn x<1500 %+6.1f  1500-2000 %+6.1f  2000-2500 %+6.1f  2500+ %+6.1f | stripe %+6.1f (dz %.0f) | kam rms strake %.1f kjol %.1f/%.1f/%.1f"
          % (name, row["front"], row["0-1500"], row["1500-2000"], row["2000-2500"], row["2500-3400"], row["bt"], dzr,
             m["rms"]["strake_lo"], m["rms"]["keel_le"], m["rms"]["keel_te"], m["rms"]["keel_bot"]), flush=True)
E.set_cam(p0, dz0, None, k0)
c.save_json(out, c.W + "/out/vurder9389_%s.json" % head9389.REF)
