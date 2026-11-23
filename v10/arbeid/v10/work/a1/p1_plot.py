import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "orig")); sys.path.insert(0, HERE)
from hr26 import curves as C0, params as P
import fit_lib as L
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
S = np.load(os.path.join(HERE, "p1_cases.npy"), allow_pickle=True).item()
D = os.path.join(HERE, "orig", "data")
raw = np.genfromtxt(os.path.join(D, "deck_halfbreadth.csv"), delimiter=",", names=True)
so = np.array(P.STERN_OUTLINE); rx, ry = raw["x_from_bow_mm"], raw["half_breadth_mm"]
m = rx < so[0, 0]; mx = np.r_[rx[m], so[:, 0]]; my = np.r_[ry[m], so[:, 1]]
xx = np.arange(0.0, so[-1, 0] + 0.01, 1.0)
fig, ax = plt.subplots(3, 1, figsize=(15, 11))
for nm, (t, c) in S.items():
    s = L.Spl(t, c)
    k = L.curvature(s, xx) * 1000
    ax[0].plot(xx, k, lw=1, label=nm)
    ax[1].plot(xx, k, lw=1, label=nm)
    ax[2].plot(mx, s(mx) - my, ".-", lw=0.6, ms=3, label=nm)
y0 = np.array([C0.deck_half_breadth(v) for v in xx])
k0 = np.gradient(np.gradient(y0, xx), xx) * 1000
ax[0].plot(xx, np.clip(k0, -2, 2), color="k", lw=0.5, alpha=0.4, label="orig (np.gradient)")
ax[0].set_ylim(-1.0, 0.3); ax[0].set_xlim(0, 7500); ax[0].legend(fontsize=7); ax[0].grid()
ax[1].set_xlim(7200, 7900); ax[1].set_ylim(-12, 2); ax[1].grid()
ax[2].plot(mx, np.array([C0.deck_half_breadth(v) for v in mx]) - my, "k.", ms=3, label="orig")
ax[2].axhspan(-12.5, 12.5, color="#eef", zorder=0); ax[2].grid(); ax[2].legend(fontsize=7)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "p1_deck_cases.png"), dpi=80)
