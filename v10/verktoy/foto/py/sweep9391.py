import sys, json; sys.path.insert(0, '.')
import numpy as np
import common as c, uwlib as U, cands
from eval9391 import score, L, R
for mode in ("E",):
    for dm in (8, 12, 16, 20, 25):
        DR = [(0.00, 45.0), (0.127, 15.0), (0.20, 6.0), (0.30, dm * 0.6), (0.45, dm), (0.70, dm), (1.00, dm)]
        cands.apply(CANOE_BOTTOM_HIDDEN=cands.hidden_aft(mode), SECTION_DEADRISE=DR)
        o = score(f"aft{mode} dr{dm}")
        print("   eL", np.round(o["eL"][::10], 0).tolist(), "eR", np.round(o["eR"][::10], 0).tolist())
    for n in (2.6, 2.2):
        DR = [(0.00, 45.0), (0.127, 15.0), (0.20, 6.0), (0.30, 9.6), (0.45, 16), (0.70, 16), (1.00, 16)]
        SN = [(0.00, 2.4), (0.15, 2.6), (0.35, n), (0.60, n), (0.80, n), (1.00, n)]
        cands.apply(CANOE_BOTTOM_HIDDEN=cands.hidden_aft(mode), SECTION_DEADRISE=DR, SECTION_N=SN)
        o = score(f"aft{mode} dr16 n{n}")
        print("   eL", np.round(o["eL"][::10], 0).tolist(), "eR", np.round(o["eR"][::10], 0).tolist())
