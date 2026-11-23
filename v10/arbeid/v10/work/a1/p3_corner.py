import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "orig")); sys.path.insert(0, HERE)
from hr26 import curves as C0, params as P
import fit_lib as L
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = os.path.join(HERE, "orig", "data")
raw = np.genfromtxt(os.path.join(D, "deck_halfbreadth.csv"), delimiter=",", names=True)
so = np.array(P.STERN_OUTLINE); rx, ry = raw["x_from_bow_mm"], raw["half_breadth_mm"]
m = rx < so[0, 0]; mx = np.r_[rx[m], so[:, 0]]; my = np.r_[ry[m], so[:, 1]]; nt = m.sum()
xx = np.arange(0.0, so[-1, 0] + 0.01, 1.0); xg = np.arange(4000.0, 6001.0, 10.0)
base = [400, 800, 1600, 2400, 3200, 4000, 4800, 5600, 6400, 7000]
VAR = {"G": [7400, 7600, 7720, 7800, 7850], "H": [7400, 7650, 7760, 7830], "I": [7300, 7550, 7700, 7790, 7850], "J": [7400, 7600, 7700, 7760, 7810, 7850]}
fig, ax = plt.subplots(1, 2, figsize=(15, 7))
for nm, st in VAR.items():
    for ws in (10.0, 30.0):
        t = L.knots(0.0, so[-1, 0], base + st)
        w = np.r_[np.ones(nt), np.full(len(so), ws)]
        s = L.fit_shape(mx, my, t, w, sign=-1, Gx=L.basis(xg, t), hx=np.full(len(xg), 0.5 * P.BEAM))
        k = L.curvature(s, xx) * 1000; r = s(mx) - my
        # glatthet i hjoernet: sum |dk/ds|
        sel = xx > 7300
        print(f"{nm} ws={ws:4.0f}: stern res {np.abs(r[nt:]).max():4.1f} trace {np.abs(r[:nt]).max():4.1f} kmin {k[sel].min():5.1f} total-variation k(7300-7891) {np.abs(np.diff(k[sel])).sum():5.1f} (monotont ville vaert {2*abs(k[sel].min()):.1f})")
        if ws == 10.0:
            ax[0].plot(xx[sel], s(xx[sel]), lw=1, label=f"{nm} {st}")
            ax[1].plot(xx[sel], k[sel], lw=1, label=nm)
ax[0].plot(so[:, 0], so[:, 1], "ko", ms=4, label="STERN_OUTLINE")
xo = np.arange(7300, 7970, 1.0); ax[0].plot(xo, [C0.deck_half_breadth(v) for v in xo], "k-", lw=0.5, label="orig")
yt = np.linspace(0, 900, 50); ax[0].plot([C0.transom_x(C0.sheer_z(7900), v) for v in yt], yt, "r--", lw=0.8, label="akterspeil i dekkshoyde")
ax[0].set_aspect("equal"); ax[0].set_xlim(7300, 7980); ax[0].set_ylim(500, 1000); ax[0].grid(); ax[0].legend(fontsize=7)
ax[1].grid(); ax[1].legend(fontsize=7); ax[1].set_ylabel("kurvatur 1/m")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "p3_corner.png"), dpi=80)
