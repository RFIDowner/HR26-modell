"""Curvature of the exact B-rep deck edge and waterlines (rebuilt loft), and
comparison with the curve functions; station positions marked."""
import sys
sys.dont_write_bytecode = True
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-curves/"
sys.path.insert(0, D + "repo")
import numpy as np
from hr26 import curves as C

ST = np.load(D + "stations.npy")
BRE = np.load(D + "brep_deckedge.npy")
WL = np.load(D + "brep_waterlines.npz")


def resample(pts, dx=5.0, x0=None, x1=None):
    x, y = pts[:, 0], pts[:, 1]
    o = np.argsort(x); x, y = x[o], y[o]
    keep = np.r_[True, np.diff(x) > 1e-6]
    x, y = x[keep], y[keep]
    xs = np.arange(x0 if x0 is not None else np.ceil(x[0]), x1 if x1 is not None else x[-1], dx)
    return xs, np.interp(xs, x, y)


def curvature(xs, ys, h=4):
    # central differences over +-h samples
    dx = xs[1] - xs[0]
    y1 = (ys[2 * h:] - ys[:-2 * h]) / (2 * h * dx)
    y2 = (ys[2 * h:] - 2 * ys[h:-h] + ys[:-2 * h]) / ((h * dx) ** 2)
    k = y2 / (1 + y1 ** 2) ** 1.5 * 1000.0   # 1/m
    return xs[h:-h], k


def signchanges(x, k, thr, lo, hi):
    m = (x >= lo) & (x <= hi) & (np.abs(k) > thr)
    s = np.sign(k[m]); xx = x[m]
    ch = np.where(np.diff(s) != 0)[0]
    return [(xx[i] + xx[i + 1]) / 2 for i in ch]


def near_station(xpk):
    d = np.abs(ST[None, :] - np.asarray(xpk)[:, None])
    return d.min(1)

# ---------------- deck edge, plan
x, y = resample(BRE[:, [0, 1]], 2.0, 6, 7840)
_, z = resample(BRE[:, [0, 2]], 2.0, 6, 7840)
f_y = np.array([C.deck_half_breadth(v) for v in x])
f_z = np.array([C.sheer_z(v) for v in x])
print("B-rep deck edge vs functions: plan dev max %.2f (x=%.0f), profile dev max %.2f (x=%.0f)" % (
    np.abs(y - f_y).max(), x[np.argmax(np.abs(y - f_y))], np.abs(z - f_z).max(), x[np.argmax(np.abs(z - f_z))]))
for lo, hi in [(6, 1000), (1000, 7100), (7100, 7400), (7400, 7840)]:
    m = (x >= lo) & (x < hi)
    i = np.argmax(np.abs(y[m] - f_y[m]))
    print(f"   x {lo}-{hi}: max plan dev {(y[m]-f_y[m])[i]:+.2f} at {x[m][i]:.0f}; max profile dev {np.abs(z[m]-f_z[m]).max():.2f}")
for h in (5, 10):
    xc, k = curvature(x, y, h)
    print(f"plan curvature (h={h*2} mm): sign changes 300-7600 (|k|>0.02/m):", [round(v) for v in signchanges(xc, k, 0.02, 300, 7600)])
xc, k = curvature(x, y, 10)
m = (xc > 40) & (xc < 700)
# local extrema of plan curvature at the bow
from numpy import r_
ext = [i for i in range(1, m.sum() - 1) if (k[m][i] - k[m][i - 1]) * (k[m][i + 1] - k[m][i]) < 0]
print("bow plan curvature extrema (x, k 1/m):", [(round(xc[m][i]), round(k[m][i], 2)) for i in ext])
m = (xc > 7000) & (xc < 7400)
print("plan curvature 7000-7400 every 20 mm:", [(round(a), round(b, 2)) for a, b in zip(xc[m][::10], k[m][::10])])
xz, kz = curvature(x, z, 10)
print("profile curvature sign changes 300-7600 (|k|>0.005/m):", [round(v) for v in signchanges(xz, kz, 0.005, 300, 7600)])
np.savez(D + "deck_curv.npz", x=xc, k=k, xz=xz, kz=kz, xd=x, yd=y, zd=z, fy=f_y, fz=f_z)

# ---------------- waterlines
for key in ["z150", "z400", "z700", "z900"]:
    pts = WL[key]
    xw, yw = resample(pts[:, [0, 1]], 2.0)
    xc, k = curvature(xw, yw, 10)
    for thr in (0.02, 0.05):
        sc = signchanges(xc, k, thr, 600, 7400)
        print(f"{key}: curvature sign changes 600-7400 (|k|>{thr}/m): {len(sc)}  at {[round(v) for v in sc]}")
    # peaks of |dk| -> local maxima of k (most positive = convex outward? sign convention: y'' < 0 is convex)
    m = (xc > 600) & (xc < 7400)
    kk, xx = k[m], xc[m]
    loc = [i for i in range(1, len(kk) - 1) if kk[i] < kk[i - 1] and kk[i] < kk[i + 1] and kk[i] < -0.3]
    print(f"   local minima of k (sharpest convex bends, k<-0.3/m): {[(round(xx[i]), round(kk[i],2)) for i in loc]}")
    print(f"   their distance to nearest station: {np.round(near_station([xx[i] for i in loc]),0)}")
    # around the forefoot
    m2 = (xc > 900) & (xc < 1300)
    i = np.argmax(np.abs(k[m2]))
    print(f"   forefoot 900-1300: max |k| {k[m2][i]:+.2f} 1/m at x={xc[m2][i]:.0f}")
    np.savez(D + f"wl_curv_{key}.npz", x=xc, k=k, xw=xw, yw=yw)
