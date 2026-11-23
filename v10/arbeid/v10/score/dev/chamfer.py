"""Silhouette (chamfer) camera fit: traced outline points -> camera."""
import sys, json, time, math
sys.path.insert(0, "..")
import numpy as np, score as S
from scipy import ndimage as ndi
from scipy.optimize import minimize
from ptool import photo, cam_from, overlay
Vs = np.load("V_skrog.npy"); Fs = np.load("F_skrog.npy")

def sil_dist(p, W, H, k):
    c = cam_from(p, W, H).scaled(k)
    fid, _ = S.raster(c, Vs, Fs)
    m = fid >= 0
    if not m.any():
        return None
    edge = m & ~ndi.binary_erosion(m)
    return ndi.distance_transform_edt(~edge) / k

def fit(name, W, H, pts, p0, fix_f=None, k=0.25, lm=None, iters=600, step=None):
    pts = np.asarray(pts, float)
    def obj(q):
        p = list(q) + ([fix_f] if fix_f is not None else [])
        d = sil_dist(p, W, H, k)
        if d is None:
            return 1e6
        u = np.clip(np.round(pts[:, 0] * k).astype(int), 0, d.shape[1] - 1)
        v = np.clip(np.round(pts[:, 1] * k).astype(int), 0, d.shape[0] - 1)
        e = d[v, u]
        tot = np.mean(np.minimum(e, 200.0) ** 2)
        if lm:
            c = cam_from(p, W, H)
            X = np.array([a for a, b in lm]); x = np.array([b for a, b in lm])
            uu, vv, _ = c.project(X)
            tot += np.mean((uu - x[:, 0]) ** 2 + (vv - x[:, 1]) ** 2)
        return tot
    q0 = list(p0[:6]) if fix_f is not None else list(p0)
    t = time.time()
    r = minimize(obj, q0, method="Powell", options=dict(maxfev=iters, xtol=1e-2, ftol=1e-3))
    p = list(r.x) + ([fix_f] if fix_f is not None else [])
    d = sil_dist(p, W, H, 0.5)
    u = np.clip(np.round(pts[:, 0] * 0.5).astype(int), 0, d.shape[1] - 1)
    v = np.clip(np.round(pts[:, 1] * 0.5).astype(int), 0, d.shape[0] - 1)
    e = d[v, u]
    print(name, "fit %.0fs nfev %d" % (time.time() - t, r.nfev), "cam", np.round(p, 2).tolist(), "silhouette err px: median %.1f max %.1f" % (np.median(e), e.max()))
    return p, e
