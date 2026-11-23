"""Re-solve IMG_9388 camera from fixed features: stem centre (u), cream line (z~0) on the stem and bow sides,
keel centre (u) and keel bottom row, topside (rail) silhouettes. Underwater outline NOT used."""
import sys, json, time; sys.path.insert(0, '.')
import numpy as np
from scipy.optimize import least_squares
import common as c, uwlib as U
C, P = c.C, c.P
t = json.load(open(c.T9388_AUTO))
st = np.array(t["stem"])[:, :2]
bt = np.array(json.load(open(c.W + "/out/bt9388.json")))
bt = bt[((bt[:, 0] >= 300) & (bt[:, 0] <= 640)) | ((bt[:, 0] >= 684) & (bt[:, 0] <= 990))]
btL = bt[bt[:, 0] < 660][:, [0, 3]]; btR = bt[bt[:, 0] > 660][:, [0, 3]]
kl = np.array(t["keel_left"]); kr = np.array(t["keel_right"])
kv = np.array(sorted(set(kl[:, 0]) & set(kr[:, 0])))
kc = np.c_[kv, 0.5 * (np.interp(kv, kl[:, 0], kl[:, 1]) + np.interp(kv, kr[:, 0], kr[:, 1]))]
kb = t["keel_bottom_v"]
rl = np.array(t["rail_left"]); rr = np.array(t["rail_right"])
rows_r = np.arange(40, 600, 8.0)
pl = np.interp(rows_r, rl[:, 0], rl[:, 1]); pr = np.interp(rows_r, rr[:, 0], rr[:, 1])
xs = np.linspace(5, 1008, 120)
STEM3 = np.c_[xs, np.zeros_like(xs), [C.bottom_z(x) for x in xs]]
zk = np.linspace(-500, -1350, 60)
KEEL3 = np.c_[2899.6 - 0.91 * zk, np.zeros_like(zk), zk]
xw = np.linspace(1010, 4200, 160)
WL = np.array([C.wl_half_breadth(x) for x in xw])
V, F = U.hull_mesh(200, 50)
Ftop = F[(V[F][:, :, 2] > 200).all(1)]

def along(cam, X3, obs, axis="v"):
    u, v, z = cam.project(X3)
    if axis == "v":           # obs = (v, u): predict u at row v
        o = np.argsort(v); a, b = v[o], u[o]
    else:                     # obs = (u, v): predict v at column u
        o = np.argsort(u); a, b = u[o], v[o]
    inside = (obs[:, 0] > a[0]) & (obs[:, 0] < a[-1])
    return np.where(inside, np.interp(obs[:, 0], a, b) - obs[:, 1], 40.0)

def residuals(p, parts=False):
    cam = U.Cam(np.r_[p[:6], 1495.0], 1500, 2000)
    zc = p[6]
    g = {}
    g["stem"] = along(cam, STEM3, st, "v")
    g["cream_stem"] = np.array([cam.project(np.array([[float(np.interp(-zc, -STEM3[:, 2], STEM3[:, 0])), 0, zc]]))[1][0] - 664.0])
    g["creamL"] = along(cam, np.c_[xw, WL, np.full_like(xw, zc)], btL, "u")
    g["creamR"] = along(cam, np.c_[xw, -WL, np.full_like(xw, zc)], btR, "u")
    g["keel_c"] = along(cam, KEEL3, kc, "v")
    g["keel_b"] = np.array([cam.project(np.array([[4450.0, 0, -1400.0]]))[1][0] - kb])
    lo, hi = U.row_extents(cam, V, Ftop, rows_r)
    g["rail_l"] = np.where(np.isfinite(lo), lo - pl, 40.0)
    g["rail_r"] = np.where(np.isfinite(hi), hi - pr, 40.0)
    g["prior"] = np.array([zc / 15.0]) * 3
    if parts:
        return g
    return np.concatenate([v / np.sqrt(max(len(v), 1) / 30.0) if k not in ("prior", "cream_stem", "keel_b") else v * 3 for k, v in g.items()])

def rms(v): return float(np.sqrt(np.mean(np.square(v))))
if __name__ == "__main__":
    best = None
    for s in ([-1500, 0, -300, -3, -2, 0, 0], [-2500, 0, -500, -3, 0, 0, 0], [-1000, 0, -200, -3, -5, 0, 0], [-2000, 0, 100, -3, 2, 0, 0], [-3000, 0, -800, -3, -3, 0, 0]):
        r = least_squares(residuals, s, bounds=([-8000, -1000, -1500, -20, -30, -10, -60], [0, 1000, 1500, 20, 30, 10, 60]),
                          x_scale=[200, 50, 100, 1, 1, 1, 10], loss="soft_l1", f_scale=4.0, max_nfev=500)
        g = residuals(r.x, True)
        print(np.round(r.x, 2).tolist(), round(r.cost, 1), {k: round(rms(v), 1) for k, v in g.items()}, flush=True)
        if best is None or r.cost < best.cost:
            best = r
    g = residuals(best.x, True)
    J = best.jac; cov = np.linalg.pinv(J.T @ J) * (2 * best.cost / max(len(best.fun) - len(best.x), 1))
    print("BEST", np.round(best.x, 2).tolist(), "sd", np.round(np.sqrt(np.diag(cov)), 2).tolist())
    c.save_json(dict(p=np.r_[best.x[:6], 1495.0], z_cream=best.x[6], rms={k: rms(v) for k, v in g.items()}), c.W + "/out/cam9388.json")
