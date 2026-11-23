import sys; sys.path.insert(0, "..")
import numpy as np, score as S
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
SP = "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-curves/"
WL = np.load(SP + "brep_waterlines.npz")
V = np.load("V_fine.npy"); F = np.load("F_fine.npy")
fn, *_ = S.face_geom(V, F)
slz = S.Slicer(V, F, 2, 10.0)
z = 700.0
p = WL["z700"]; p = p[np.argsort(p[:, 0])]
xg = np.arange(0, 8000, 5.0)
yb = np.interp(xg, p[:, 0], p[:, 1], left=np.nan, right=np.nan)
xf, yf, _ = S.waterline(slz, z, fn)
sec = slz.section(z)
P = np.r_[sec["P0"], sec["P1"]]
m = (P[:, 1] > 0) & (P[:, 0] > 2000) & (P[:, 0] < 4000)
# raw polyline vertices on the outer side
fig, ax = plt.subplots(3, 1, figsize=(16, 11))
mm = (xg > 2000) & (xg < 4000)
ax[0].plot(xg[mm], (yf - yb)[mm], 'b-', lw=0.8, label='fine STL - brep (mm)')
ax[0].legend(); ax[0].grid()
for nm, y, c in (("brep", yb, 'k'), ("fine", yf, 'b')):
    mmm = (xg >= 600) & (xg <= 7400)
    k, _ = S.curvature_graph(xg[mmm], y[mmm], 25.0)
    ax[1].plot(xg[mmm], k, c + '-', lw=0.8, label=nm)
ax[1].set_ylim(-0.6, 0.6); ax[1].axhline(0.02, color='r', lw=0.5); ax[1].axhline(-0.02, color='r', lw=0.5); ax[1].legend(); ax[1].grid()
# vertex spacing of the STL section polyline near y max
xs = np.sort(P[(P[:,1] > 500), 0])
ax[2].plot(xs[1:], np.diff(xs), 'g.', ms=2); ax[2].set_yscale('log'); ax[2].set_title('spacing of section vertices along x (outer + inner)'); ax[2].grid()
fig.savefig("wl_noise.png", dpi=70)
print("brep pts spacing", np.median(np.diff(p[:,0])))
