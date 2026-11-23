import sys, json
sys.path.insert(0, sys.argv[1])
from hr26 import params as P, curves as C
sys.path.insert(1, '.')
import numpy as np
import common as c, uwlib as U, photos as PH
V, F = PH.mesh()
out = {}
for name, cam in (("9391", PH.CAM91), ("9388", PH.CAM88["s2"])):
    rows = np.arange(0, 2000, 3.0)
    lo, hi = U.row_extents(cam, V, F, rows)
    secs = {}
    for x in (3000, 4300, 5600, 6600, 7400, 7750):
        s = np.array(C.section(float(x), 60)); s2 = s[::-1].copy(); s2[:, 0] *= -1
        ss = np.vstack([s2, s[1:]]); X = np.c_[np.full(len(ss), float(x)), ss]
        X[:, 0] = np.minimum(X[:, 0], U.transom_x(X[:, 2], X[:, 1]))
        u, v, z = cam.project(X); m = ss[:, 1] < 250
        secs[str(x)] = np.c_[u[m], v[m]].tolist()
    out[name] = dict(rows=rows.tolist(), lo=lo.tolist(), hi=hi.tolist(), secs=secs)
c.save_json(out, c.W + f"/out/outl_{sys.argv[2]}.json")
