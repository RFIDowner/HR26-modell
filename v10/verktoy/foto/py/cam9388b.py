import sys, json; sys.path.insert(0, '.')
import numpy as np
from scipy.optimize import least_squares
import cam9388 as K, uwlib as U, common as c
def res(q, parts=False, w_rail=1.0):
    cam_f = q[7]
    orig = U.Cam
    g = None
    p = np.r_[q[:6], q[6]]
    # temporarily use f = q[7]
    class Cf(orig):
        def __init__(self, pp, W, H):
            super().__init__(np.r_[pp[:6], cam_f], W, H)
    U.Cam = Cf
    try:
        g = K.residuals(p, True)
    finally:
        U.Cam = orig
    g["prior"] = np.array([q[6] / 15.0, (cam_f - 1495) / 100.0]) * 3
    g["rail_l"] = g["rail_l"] * w_rail; g["rail_r"] = g["rail_r"] * w_rail
    if parts:
        return g
    return np.concatenate([v / np.sqrt(max(len(v), 1) / 30.0) if k not in ("prior", "cream_stem", "keel_b") else v * 3 for k, v in g.items()])
for w_rail in (1.0, 0.0):
    best = None
    for s in ([-781, -12, -298, -3.26, 0.85, 0.13, 0, 1495], [-1500, 0, -400, -3.3, 1, 0, 0, 1800], [-2500, 0, -500, -3.3, 1, 0, 0, 2300], [-500, 0, -300, -3.3, 0, 0, 0, 1200]):
        r = least_squares(lambda q: res(q, False, w_rail), s, bounds=([-8000, -1000, -1500, -20, -30, -10, -60, 900], [0, 1000, 1500, 20, 30, 10, 60, 3500]),
                          x_scale=[200, 50, 100, 1, 1, 1, 10, 50], loss="soft_l1", f_scale=4.0, max_nfev=500)
        if best is None or r.cost < best.cost:
            best = r
    g = res(best.x, True, 1.0)
    print("w_rail", w_rail, np.round(best.x, 2).tolist(), round(best.cost, 1), {k: round(K.rms(v), 1) for k, v in g.items()}, flush=True)
    c.save_json(dict(p=np.r_[best.x[:6], best.x[7]], z_cream=best.x[6], rms={k: K.rms(v) for k, v in g.items()}), c.W + f"/out/cam9388_rail{int(w_rail)}.json")
