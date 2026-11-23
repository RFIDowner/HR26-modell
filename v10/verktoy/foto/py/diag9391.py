import sys, json; sys.path.insert(0, '.')
import numpy as np
import common as c, uwlib as U, cands
cam = U.Cam(json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"][:7], 1500, 2000)
t = json.load(open(c.W + "/out/t9391.json")); ro = np.array(t["red_outline"], float)
def sec_cross(x, v):
    s = np.array(c.C.section(x, 120)); s2 = s[::-1].copy(); s2[:, 0] *= -1
    ss = np.vstack([s2, s[1:]])
    X = np.c_[np.full(len(ss), x), ss]
    X[:, 0] = np.minimum(X[:, 0], U.transom_x(X[:, 2], X[:, 1]))
    u, vv, z = cam.project(X)
    us, ys, zs = [], [], []
    for i in range(len(vv) - 1):
        if (vv[i] - v) * (vv[i + 1] - v) <= 0 and vv[i] != vv[i + 1]:
            f = (v - vv[i]) / (vv[i + 1] - vv[i])
            us.append(u[i] + f * (u[i + 1] - u[i])); ys.append(X[i, 1] + f * (X[i + 1, 1] - X[i, 1])); zs.append(X[i, 2] + f * (X[i + 1, 2] - X[i, 2]))
    if not us:
        return None
    k = int(np.argmin(us))
    return us[k], ys[k], zs[k]
def report(tag):
    print(tag)
    for v in (760, 800, 850, 900, 935):
        best = None
        for x in np.arange(3000, 7900, 100):
            r = sec_cross(float(x), v)
            if r and (best is None or r[0] < best[1]):
                best = (x, *r)
        obs = np.interp(v, ro[:, 0], ro[:, 1])
        print(f"  row {v}: model left u {best[1]:6.1f} at x {best[0]} (y {best[2]:6.0f}, z {best[3]:6.0f})   photo u {obs:6.1f}  -> {best[1]-obs:+6.1f} px; bottom_z(x)={c.C.bottom_z(best[0]):.0f}")
report("today")
DR = [(0.00, 45.0), (0.127, 15.0), (0.20, 6.0), (0.30, 9.6), (0.45, 16), (0.70, 16), (1.00, 16)]
cands.apply(CANOE_BOTTOM_HIDDEN=cands.hidden_aft("E"), SECTION_DEADRISE=DR)
report("aftE dr16")
