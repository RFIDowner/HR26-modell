"""Solve the IMG_9391 camera from features the underwater work does not move:
strake across the transom (z 805), boot-top blue top edge and cream lower edge on the transom face (z free, cream prior 0),
left topside silhouette above the boot-top, rudder centre plane (y=0). The red underwater outline is NOT used."""
import sys, json, time; sys.path.insert(0, '.')
import numpy as np
from scipy.optimize import least_squares
import common as c, uwlib as U
P, C = c.P, c.C
W_, H_ = 1500, 2000
t = json.load(open(c.W + "/out/t9391.json"))
sil = json.load(open(c.W + "/out/sil9391.json"))
rud = np.array(json.load(open(c.W + "/out/rud9391.json")))
st = np.array(t["strake"]); st_c = np.c_[st[:, 0], 0.5 * (st[:, 1] + st[:, 2])]
bt = np.array(t["boottop"], float)
flat = ((bt[:, 0] >= 330) & (bt[:, 0] <= 570)) | ((bt[:, 0] >= 730) & (bt[:, 0] <= 940))
bt_top = bt[flat][:, [0, 1]]; bt_cr = bt[flat][:, [0, 3]]
silL = np.array(sil["left"])[:, :2]
silL = silL[(silL[:, 0] >= 480) & (silL[:, 0] <= 690)]
rud = rud[(rud[:, 0] >= 1010) & (rud[:, 0] <= 1430)]
rud_c = np.c_[rud[:, 0], 0.5 * (rud[:, 1] + rud[:, 2])]

ys = np.linspace(-520, 520, 105)
def tline(z, ys=ys, dx=0.0):
    return np.c_[[U.transom_x(z, y) + dx for y in ys], ys, np.full(len(ys), z)]
STRAKE3 = tline(805.0, dx=13.0)
ysb = np.linspace(-450, 450, 91)
RUD3 = np.c_[np.full(60, 8120.0), np.zeros(60), np.linspace(-1094, -60, 60)]
V, F = U.hull_mesh(200, 50)
Zf = V[F][:, :, 2]
Ftop = F[(Zf > 30).all(1)]

def curve_resid(cam, X3, obs, along="u"):
    u, v, z = cam.project(X3)
    if along == "u":
        o = np.argsort(u); uu, vv = u[o], v[o]
        inside = (obs[:, 0] > uu[0]) & (obs[:, 0] < uu[-1])
        pred = np.interp(obs[:, 0], uu, vv)
        return np.where(inside, pred - obs[:, 1], 40.0)
    o = np.argsort(v); uu, vv = u[o], v[o]
    inside = (obs[:, 0] > vv[0]) & (obs[:, 0] < vv[-1])
    pred = np.interp(obs[:, 0], vv, uu)
    return np.where(inside, pred - obs[:, 1], 40.0)

def residuals(p, parts=False):
    cam = U.Cam(p[:7], W_, H_)
    zt, zc = p[7], p[8]
    g = {}
    g["strake"] = curve_resid(cam, STRAKE3, st_c)
    g["bt_top"] = curve_resid(cam, tline(zt, ysb), bt_top)
    g["bt_cream"] = curve_resid(cam, tline(zc, ysb), bt_cr)
    lo, hi = U.row_extents(cam, V, Ftop, silL[:, 0])
    g["silL"] = np.where(np.isfinite(lo), lo - silL[:, 1], 40.0)
    g["rudder"] = curve_resid(cam, RUD3, rud_c, along="v")
    g["prior"] = np.array([(p[6] - 1495.0) / 40.0, zc / 25.0]) * 3.0
    if parts:
        return g
    w = dict(strake=1.0, bt_top=1.0, bt_cream=1.0, silL=1.0, rudder=1.0, prior=1.0)
    return np.concatenate([w[k] * v / np.sqrt(max(len(v), 1) / 30.0) if k != "prior" else v for k, v in g.items()])

def rms(v): return float(np.sqrt(np.mean(np.square(v))))

if __name__ == "__main__":
    p0 = [9893.5, 0.0, -355.2, 174.14, 5.74, -3.38, 1490.0, 150.0, 0.0]
    print("score.py cam:", {k: round(rms(v), 1) for k, v in residuals(p0, True).items()})
    best = None
    starts = [p0]
    for X, Z, pit, f in ((9500, -300, 3, 1495), (10500, -400, 6, 1495), (9800, 0, 10, 1495), (11000, -700, 2, 1600), (9200, -600, 0, 1400)):
        starts.append([X, 0.0, Z, 175.0, pit, -3.0, f, 150.0, 0.0])
    lb = [8300, -1500, -1300, 160, -20, -15, 1100, 0, -100]
    ub = [14000, 1500, 1500, 190, 30, 15, 2200, 400, 100]
    for s in starts:
        t0 = time.time()
        r = least_squares(residuals, s, bounds=(lb, ub), x_scale=[200, 50, 100, 1, 1, 1, 50, 20, 10], loss="soft_l1", f_scale=4.0, max_nfev=400)
        g = residuals(r.x, True)
        print("->", np.round(r.x, 2).tolist(), "cost %.1f" % r.cost, {k: round(rms(v), 1) for k, v in g.items()}, "%.0fs" % (time.time() - t0), flush=True)
        if best is None or r.cost < best.cost:
            best = r
    g = residuals(best.x, True)
    c.save_json(dict(p=best.x, keys=["x", "y", "z", "yaw", "pitch", "roll", "f", "z_bt_top", "z_cream"],
                     rms={k: rms(v) for k, v in g.items()}, cost=best.cost), c.W + "/out/cam9391.json")
    print("BEST", np.round(best.x, 2).tolist())
