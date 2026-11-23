import sys, json, time; sys.path.insert(0, '.')
import numpy as np
from scipy.optimize import least_squares
import common as c, opt
def run(tag, q0, lb, ub, smooth=2.0, w88=0.4):
    opt.W88S = w88
    def r2(q):
        v = opt.resid(q)
        d = np.array(q[:7]); n = np.array(q[7:9])
        return np.r_[v, np.diff(d, 2) * smooth, (n - 3.4) * 2.0]
    t0 = time.time()
    r = least_squares(r2, q0, bounds=(lb, ub), x_scale=[2, 2, 2, 2, 2, 2, 2, 0.2, 0.2, 15, 15, 30], diff_step=1e-3, max_nfev=60, loss="soft_l1", f_scale=3.0)
    g, info = opt.resid(r.x, True)
    a, b = info["e91"]; l8, r8, b8 = info["e88"]
    f = lambda e: f"{np.mean(e):+6.1f}/{np.sqrt(np.mean(e**2)):5.1f}"
    print(tag, "q", np.round(r.x, 1).tolist(), "cost", round(r.cost, 1), "%.0fs" % (time.time() - t0))
    print("    9391 L", f(a), "R", f(b), "| 9388 L", f(l8), "R", f(r8), "bot", f(b8), "| vol %.3f top %.1f" % (info["vol"], info["top"]), flush=True)
    return r.x, info
q0 = [4.0, 8.0, 14.0, 18.0, 20.0, 20.0, 20.0, 3.4, 3.3, -390.0, -280.0, 300.0]
lb = [0, 0, 0, 0, 0, 0, 0, 2.8, 2.8, -460, -330, 200]
ub = [30, 30, 30, 30, 30, 30, 30, 4.2, 4.2, -300, -200, 420]
res = {}
for tag, sm, w88 in (("A smooth2 w88=0.4", 2.0, 0.4), ("B smooth2 w88=0", 2.0, 0.0)):
    q, info = run(tag, q0, lb, ub, sm, w88)
    res[tag] = dict(q=q, vol=info["vol"], top=info["top"])
c.save_json(res, c.W + "/out/opt2.json")
