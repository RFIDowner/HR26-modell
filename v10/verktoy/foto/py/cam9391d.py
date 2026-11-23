import sys, json; sys.path.insert(0, '.')
import numpy as np
from scipy.optimize import least_squares
import cam9391 as K, uwlib as U, common as c
K.st_c = K.st_c[np.abs(K.st_c[:, 0] - 640) < 270]
def res2(q, parts=False, zc_sig=5.0):
    K.STRAKE3 = K.tline(q[9], dx=13.0)
    g = K.residuals(q[:9], True)
    g["prior"] = np.array([(q[6] - 1495.0) / 10.0, q[8] / zc_sig, (q[9] - 805.0) / 60.0]) * 3.0
    if parts:
        return g
    return np.concatenate([v / np.sqrt(max(len(v), 1) / 30.0) if k != "prior" else v for k, v in g.items()])
res = json.load(open(c.W + "/out/cam9391.json"))
for zc_sig in (5.0, 25.0):
    best = None
    for s in ([9700, 0, -120, 176, 5, 1, 1495, 140, 0, 805], [9733, -37, -120, 174.9, 6.7, 1.0, 1493, 92, 0, 752], [10300, 0, -300, 176, 3, 1.5, 1495, 140, 0, 760]):
        r = least_squares(lambda q: res2(q, False, zc_sig), s, bounds=([8300, -1500, -1300, 160, -20, -15, 1100, 0, -100, 500], [14000, 1500, 1500, 190, 30, 15, 2200, 400, 100, 1000]),
                          x_scale=[200, 50, 100, 1, 1, 1, 50, 20, 10, 20], loss="soft_l1", f_scale=4.0, max_nfev=500)
        if best is None or r.cost < best.cost:
            best = r
    gg = res2(best.x, True, zc_sig)
    print("zc_sig", zc_sig, np.round(best.x, 2).tolist(), round(best.cost, 1), {k: round(K.rms(v), 2) for k, v in gg.items()})
    # parameter uncertainty from the Jacobian (unit-weight scaled)
    J = best.jac; cov = np.linalg.pinv(J.T @ J) * (2 * best.cost / max(len(best.fun) - len(best.x), 1))
    print("   sd x,y,z:", np.round(np.sqrt(np.diag(cov))[:3], 1).tolist(), "pitch", round(float(np.sqrt(cov[4, 4])), 2))
    res["zc%d" % int(zc_sig)] = dict(p=best.x, rms={k: K.rms(v) for k, v in gg.items()}, sd=np.sqrt(np.diag(cov)))
c.save_json(res, c.W + "/out/cam9391.json")
