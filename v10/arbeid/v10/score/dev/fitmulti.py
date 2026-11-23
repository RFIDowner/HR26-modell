"""Multi-start silhouette fit with selectable free parameters (light workers)."""
import sys, json, time, math
sys.path.insert(0, "..")
import numpy as np
from concurrent.futures import ProcessPoolExecutor

NAMES = ["x", "y", "z", "yaw", "pitch", "roll", "f"]

def cam_from(p, W, H):
    import score as S
    return S.Cam(np.array(p[:3], float), S.rot_from_euler(p[3], p[4], p[5]), W, H, f=p[6], cx=W / 2.0, cy=H / 2.0)

def _obj_factory(W, H, pts, base, free, k):
    import score as S
    from scipy import ndimage as ndi
    Vs = np.load("V_skrog.npy"); Fs = np.load("F_skrog.npy")
    pts = np.asarray(pts, float)
    def full(q):
        p = list(base)
        for i, n in enumerate(free):
            p[NAMES.index(n)] = q[i]
        return p
    def obj(q):
        p = full(q)
        c = cam_from(p, W, H).scaled(k)
        fid, _ = S.raster(c, Vs, Fs)
        m = fid >= 0
        if m.sum() < 50:
            return 1e7
        edge = m & ~ndi.binary_erosion(m)
        d = ndi.distance_transform_edt(~edge) / k
        px, py = pts[:, 0] * k, pts[:, 1] * k
        inside = (px >= 0) & (px < d.shape[1]) & (py >= 0) & (py < d.shape[0])
        u = np.clip(np.round(px).astype(int), 0, d.shape[1] - 1)
        v = np.clip(np.round(py).astype(int), 0, d.shape[0] - 1)
        e = np.where(inside, d[v, u], 300.0)
        return float(np.mean(np.minimum(e, 300.0) ** 2))
    return obj, full

def run_one(args):
    W, H, pts, base, free, bounds, q0, k, iters = args
    from scipy.optimize import minimize
    obj, full = _obj_factory(W, H, pts, base, free, k)
    r = minimize(obj, q0, method="Powell", bounds=bounds, options=dict(maxfev=iters, xtol=5e-2, ftol=1e-3))
    return float(r.fun), full(list(r.x)), int(r.nfev)

def multistart(name, W, H, pts, base, free, bounds, starts, k=0.15, iters=350, workers=2):
    t = time.time()
    jobs = [(W, H, pts, base, free, bounds, s, k, iters) for s in starts]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(run_one, jobs))
    res.sort(key=lambda r: r[0])
    for f, p, n in res:
        print(name, "rms %.1f px" % math.sqrt(f), "nfev", n, np.round(p, 2).tolist(), flush=True)
    print(name, "took %.0fs" % (time.time() - t), flush=True)
    return res[0]
