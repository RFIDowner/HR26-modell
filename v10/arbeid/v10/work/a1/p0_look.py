"""Ser paa raadata mot dagens kurver (orig)."""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "orig"))
from hr26 import curves as C0, params as P
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
uw = np.loadtxt(os.path.join(HERE, "orig/data/uw_station.csv"), delimiter=",", skiprows=1)
hs = np.genfromtxt(os.path.join(HERE, "orig/data/hull_stations.csv"), delimiter=",", names=True)
xx = np.arange(0, 7951, 5.0)
zb0 = np.array([C0.bottom_z(v) for v in xx])
fig, ax = plt.subplots(2, 1, figsize=(15, 9))
ax[0].plot(uw[:, 0], -uw[:, 1], ".", ms=1.5, label="uw_station.csv (traced)")
ax[0].plot(hs["x_from_bow_mm"], hs["canoe_bottom_z_mm"], "o", ms=3, label="hull_stations canoe_bottom")
ax[0].plot(xx, zb0, "-", lw=1, label="bottom_z (orig)")
ax[0].set_ylim(-1500, 1300); ax[0].legend(); ax[0].grid()
sel = (uw[:, 0] < 3500)
ax[1].plot(uw[sel, 0], -uw[sel, 1], ".", ms=2, label="uw trace")
ax[1].plot(xx[xx < 3500], zb0[xx < 3500], "-", label="bottom_z orig")
ax[1].plot(hs["x_from_bow_mm"], hs["canoe_bottom_z_mm"], "o", ms=3)
ax[1].set_xlim(0, 3500); ax[1].set_ylim(-700, 1300); ax[1].grid(); ax[1].legend()
fig.tight_layout(); fig.savefig(os.path.join(HERE, "p0_profile.png"), dpi=90)
# tall
for x0 in [5600, 5700, 5750, 5800, 5850, 5900, 6000, 6100, 6200, 6300, 6400, 6500, 6600, 6700, 6800, 7000, 7200, 7300, 7350, 7400, 7450, 7500]:
    i = np.argmin(abs(uw[:, 0] - x0)); print(x0, round(-uw[i, 1], 1), round(C0.bottom_z(x0), 1))
