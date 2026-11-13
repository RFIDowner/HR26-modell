import sys, json; sys.path.insert(0, '.')
import numpy as np
import common as c, uwlib as U, cands
from eval9391 import score
def run(tag, **kw):
    cands.apply(**kw); o = score(tag)
    print("   eL", np.round(o["eL"][::8], 0).tolist(), " eR", np.round(o["eR"][::8], 0).tolist())
run("today")
for mode in ("E",):
    H = cands.hidden_aft(mode)
    for d1, d2 in ((16, 30), (16, 40), (20, 45), (16, 50)):
        DR = [(0.00, 45.0), (0.127, 15.0), (0.20, 6.0), (0.30, 10), (0.50, d1), (0.70, d1 + 0.4 * (d2 - d1)), (0.85, d1 + 0.8 * (d2 - d1)), (1.00, d2)]
        run(f"aft{mode} dr{d1}->{d2}", CANOE_BOTTOM_HIDDEN=H, SECTION_DEADRISE=DR)
