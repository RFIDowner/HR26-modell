import sys; sys.path.insert(0, "..")
import numpy as np, score as S
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
V = np.load("V_fine.npy"); F = np.load("F_fine.npy")
fn, *_ = S.face_geom(V, F)
slx = S.Slicer(V, F, 0, 10.0)
xs = np.arange(20.0, 7900.0, 10.0)
zl = []
for x in xs:
    sec = slx.section(x)
    pts = np.r_[sec["P0"], sec["P1"]]
    cl = np.abs(pts[:, 1]) < 800
    zl.append(pts[cl, 2].min())
zl = np.array(zl)
fig, ax = plt.subplots(2, 1, figsize=(16, 9))
ax[0].plot(S._UW[:, 0], -S._UW[:, 1], 'r.-', ms=2, label='uw_station (trace)')
ax[0].plot(xs, zl, 'b-', label='model lowest point per x')
ax[0].plot(S._HS[:, 0], S._HS[:, 3], 'g.--', label='hull_stations canoe_bottom')
ax[0].legend(); ax[0].grid(); ax[0].set_aspect('equal')
m = (xs > 900) & (xs < 2000)
ax[1].plot(S._UW[:, 0], -S._UW[:, 1], 'r.-', ms=2)
ax[1].plot(xs, zl, 'b-'); ax[1].set_xlim(900, 2000); ax[1].set_ylim(-400, 100); ax[1].grid()
fig.savefig("uw_vs_model.png", dpi=70)
for x0 in [1010, 1050, 1100, 1200, 1300, 1500, 2000, 3000, 3400, 3600, 3900, 4200, 4600, 5000, 5600]:
    i = np.argmin(abs(xs - x0)); print(x0, round(zl[i], 1), "data", round(-np.interp(x0, S._UW[:,0], S._UW[:,1]), 1))
