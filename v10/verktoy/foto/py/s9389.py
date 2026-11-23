"""Grovsoek etter kameraet for IMG_9389 fra mange startpunkter (cam9389.residuals,
modus 'utenbt'). Skriver de beste til ../out/s9389.json."""
import json
import math
import sys
import time

import numpy as np
from scipy.optimize import least_squares

import head9389  # noqa: F401
import common as c
import cam9389 as K

t0 = time.time()
res = []
nfev = int(sys.argv[1]) if len(sys.argv) > 1 else 40
for cx in (500.0, 1500.0, 2500.0):
    for cy in (2000.0, 3000.0, 4500.0):
        for cz in (-800.0, -450.0, -100.0):
            for f in (1100.0, 1500.0):
                tx, ty, tz = 4300.0, 0.0, -300.0
                yaw = math.degrees(math.atan2(ty - cy, tx - cx))
                pitch = -math.degrees(math.atan2(tz - cz, math.hypot(tx - cx, ty - cy)))
                s = [cx, cy, cz, yaw, pitch, 0.0, f]
                try:
                    r = least_squares(lambda q: K.residuals(q, mode="utenbt", f0=f, fs=400.0), s, x_scale=K.XS[:7],
                                      loss="soft_l1", f_scale=2.0, max_nfev=nfev, diff_step=1e-5)
                except Exception as e:  # noqa
                    print("feil", s, e)
                    continue
                g = K.residuals(r.x, True, "utenbt", f0=f, fs=400.0)
                res.append(dict(start=s, x=r.x, cost=float(r.cost), rms={k: round(K.rms(v), 1) for k, v in g.items()}))
                print("%7.1f  %s  %s  (%.0f s)" % (r.cost, np.round(r.x, 1).tolist(), res[-1]["rms"], time.time() - t0),
                      flush=True)
res.sort(key=lambda d: d["cost"])
c.save_json(res[:15], c.W + "/out/s9389.json")
