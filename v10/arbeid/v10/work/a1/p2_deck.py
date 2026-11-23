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
m = rx < so[0, 0]; mx = np.r_[rx[m], so[:, 0]]; my = np.r_[ry[m], so[:, 1]]
nt = m.sum(); art = (mx > 2450) & (mx < 3250)
xx = np.arange(0.0, so[-1, 0] + 0.01, 1.0)
xg = np.arange(4000.0, 6001.0, 10.0)
HB = 0.5 * P.BEAM
def run(nm, KN, ws, lam, beam=True):
    t = L.knots(0.0, so[-1, 0], KN)
    w = np.r_[np.ones(nt), np.full(len(so), ws)]
    kw = dict(Gx=L.basis(xg, t), hx=np.full(len(xg), HB)) if beam else {}
    s = L.fit_shape(mx, my, t, w, lam=lam, sign=-1, **kw)
    yy = s(xx); k = L.curvature(s, xx); r = s(mx) - my
    i = np.argmax(np.abs(r))
    print(f"{nm:28s} beam {2*yy.max():7.1f}@{xx[yy.argmax()]:4.0f} max|res| {np.abs(r).max():5.1f} at x={mx[i]:.0f}  trace-utenom-art {np.abs(r[:nt][~art[:nt]]).max():4.1f} stern {np.abs(r[nt:]).max():4.1f}  corner kmin {k[xx>7600].min()*1000:5.1f}/m  signchg {len(L.sign_changes(xx, k, 1e-6))}")
    return s
V = {}
#V["C"] = run("C (baug+tette hekk)", [150,400,800,1600,2400,3200,4000,4800,5600,6400,7000,7400,7600,7700,7760,7800,7830,7860], 100.0, 0.0)
#V["E"] = run("E (faerre hekk)", [150,400,800,1600,2400,3200,4000,4800,5600,6400,7000,7400,7650,7780,7840], 10.0, 0.0)
#V["F"] = run("F (E, uten 150)", [400,800,1600,2400,3200,4000,4800,5600,6400,7000,7400,7650,7780,7840], 10.0, 0.0)
V["G"] = run("G (F + 7700)", [400,800,1600,2400,3200,4000,4800,5600,6400,7000,7400,7600,7720,7800,7850], 10.0, 0.0)
for lam in [1e9, 1e10, 1e11, 1e12, 1e13]:
    V[f"P{lam:.0e}"] = run(f"P tett+jerk lam={lam:.0e}", [100,200,300,400,600,800,1100,1400,1800,2200,2600,3000,3400,3800,4200,4600,5000,5400,5800,6200,6600,7000,7300,7500,7600,7680,7740,7790,7830,7860], 10.0, lam)
np.save(os.path.join(HERE, "p2_cases.npy"), {k: (v.t, v.c) for k, v in V.items()}, allow_pickle=True)
fig, ax = plt.subplots(3, 1, figsize=(15, 11))
for nm, s in V.items():
    k = L.curvature(s, xx) * 1000
    ax[0].plot(xx, k, lw=1, label=nm); ax[1].plot(xx, k, lw=1, label=nm)
    ax[2].plot(mx, s(mx) - my, ".-", lw=0.6, ms=3, label=nm)
ax[0].set_ylim(-1.0, 0.1); ax[0].set_xlim(0, 7500); ax[0].legend(fontsize=7, ncol=4); ax[0].grid()
ax[1].set_xlim(7200, 7900); ax[1].set_ylim(-12, 1); ax[1].grid()
ax[2].axhspan(-12.5, 12.5, color="#eef", zorder=0); ax[2].grid(); ax[2].legend(fontsize=7, ncol=4)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "p2_deck_cases.png"), dpi=80)
