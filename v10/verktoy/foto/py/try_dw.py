import sys; sys.path.insert(0, '.')
import numpy as np
import common as c, cands, dw, photos as PH
PH.summary("today")
H = cands.hidden_aft("E")
def interp(tab):
    a = np.array(tab, float); return lambda x: float(np.interp(x, a[:, 0], a[:, 1]))
for zc_t, d1, wdw in ((-290, 16, 300), (-300, 18, 250), (-320, 18, 350), (-300, 14, 300)):
    DR = [(0.00, 45.0), (0.127, 15.0), (0.20, 6.0), (0.30, 10), (0.45, d1), (1.00, d1)]
    C = cands.apply(CANOE_BOTTOM_HIDDEN=H, SECTION_DEADRISE=DR)
    prof = C.bottom_z
    zc = interp([(5600, -470), (6200, -440), (6800, -390), (7300, zc_t - 40 + 0.5 * 40), (7800, zc_t)])
    dw.install(C, lambda x: max(0.0, zc(x) - prof(x)) if x > 5600 else 0.0, lambda x: wdw)
    PH.summary(f"dw zc{zc_t} dr{d1} w{wdw}")
