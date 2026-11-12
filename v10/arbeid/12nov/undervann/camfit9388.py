"""Re-solve the IMG_9388 camera from features the underwater work does not move.

Free: camera centre (x, y, z), yaw, pitch, roll, focal length f.
Residuals (photo px):
  rail   - outer edge of the dark rub-rail band, rows 0..630, vs the outer
           silhouette of today's hull (int4 STL, topsides incl. the rail)
  stem   - centre of the stem highlight, rows 0..480, vs the stem profile
           (curves.bottom_z for x < LWL_FWD, y = 0)
  keel   - fin centre (mean of the traced edges) and fin bottom row vs the
           keel fin of the STL (z < -600)
The underwater hull outline is NOT used.
"""
import sys, json, time
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/undervann/py")
import numpy as np
from scipy.optimize import least_squares
import uw

NAME = "IMG_9388"
t = json.load(open(uw.OUT + "/traces/t9388_auto.json"))
V, F = uw.load_int4()
Z = V[F][:, :, 2]
top = (Z > 250).all(1)
Vt, Ft = V, F[top]
keel = (Z < -620).all(1)
Fk = F[keel]
Vk_pts = V[np.unique(Fk)]

rl = np.array(t["rail_left"]); rr = np.array(t["rail_right"])
rows_r = np.arange(0, 632, 2.0)
pl = np.interp(rows_r, rl[:, 0], rl[:, 1])
pr = np.interp(rows_r, rr[:, 0], rr[:, 1])
st = np.array(t["stem"])
kl = np.array(t["keel_left"]); kr = np.array(t["keel_right"])
krows = np.array(sorted(set(kl[:, 0]) & set(kr[:, 0])))
kc = 0.5 * (np.interp(krows, kl[:, 0], kl[:, 1]) + np.interp(krows, kr[:, 0], kr[:, 1]))
kw = np.interp(krows, kr[:, 0], kr[:, 1]) - np.interp(krows, kl[:, 0], kl[:, 1])
kb = t["keel_bottom_v"]
xs_stem = np.linspace(20.0, 1000.0, 300)
stem3 = np.c_[xs_stem, np.zeros_like(xs_stem), [uw.C.bottom_z(x) for x in xs_stem]]


def residuals(p, parts=False):
    cam = uw.cam_from(p, NAME)
    lo, hi, _, _ = uw.row_extents(cam, Vt, Ft, rows_r)
    e_l = np.where(np.isfinite(lo), lo - pl, 60.0)
    e_r = np.where(np.isfinite(hi), hi - pr, -60.0)
    u, v, z = cam.project(stem3)
    o = np.argsort(v)
    us = np.interp(st[:, 0], v[o], u[o], left=np.nan, right=np.nan)
    e_s = np.where(np.isfinite(us), us - st[:, 1], 60.0)
    klo, khi, _, _ = uw.row_extents(cam, V, Fk, krows)
    e_kc = np.where(np.isfinite(klo), 0.5 * (klo + khi) - kc, 60.0)
    e_kw = np.where(np.isfinite(klo), (khi - klo) - kw, 60.0)
    _, vk, _ = cam.project(Vk_pts)
    e_kb = np.array([vk.max() - kb])
    groups = dict(rail_l=e_l, rail_r=e_r, stem=e_s, keel_c=e_kc, keel_w=e_kw, keel_b=e_kb)
    if parts:
        return groups
    w = dict(rail_l=1.0, rail_r=1.0, stem=1.0, keel_c=1.0, keel_w=0.3, keel_b=1.0)
    n0 = 60.0
    return np.concatenate([w[k] * g / np.sqrt(max(len(g), 1) / n0) for k, g in groups.items()])


def rms(g):
    return float(np.sqrt(np.mean(np.square(g)))) if len(g) else float("nan")


if __name__ == "__main__":
    p0 = uw.cam_params0(NAME)
    print("score.py camera:", np.round(p0, 2).tolist())
    print({k: round(rms(g), 1) for k, g in residuals(p0, True).items()})
    starts = [p0]
    for cx, cz, pit, f in ((-800, -300, 3, 1700), (-1500, -600, 0, 1900), (-1500, -300, 2, 1700),
                           (-2500, -600, 0, 2300), (-400, -200, 4, 1600)):
        starts.append([cx, 0.0, cz, -3.0, pit, 0.3, f])
    best = None
    lb = [-6000, -600, -1400, -15, -25, -8, 1000]
    ub = [500, 600, 800, 15, 30, 8, 4000]
    for s in starts:
        t0 = time.time()
        r = least_squares(residuals, s, bounds=(lb, ub), x_scale=[200, 50, 100, 1, 1, 1, 100],
                          loss="soft_l1", f_scale=8.0, max_nfev=300)
        g = residuals(r.x, True)
        print("start", np.round(s, 1).tolist(), "->", np.round(r.x, 2).tolist(), "cost %.1f" % r.cost,
              {k: round(rms(v), 1) for k, v in g.items()}, "%.0fs" % (time.time() - t0), flush=True)
        if best is None or r.cost < best.cost:
            best = r
    p = best.x.tolist()
    g = residuals(p, True)
    res = dict(name=NAME, p=p, keys=["x", "y", "z", "yaw", "pitch", "roll", "f"],
               rms={k: rms(v) for k, v in g.items()}, cost=float(best.cost))
    uw.save_json(res, uw.OUT + "/traces/cam9388.json")
    print("BEST", res)
