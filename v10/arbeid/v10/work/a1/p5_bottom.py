import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "orig")); sys.path.insert(0, HERE)
from hr26 import curves as C0, params as P
import fit_lib as L
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = os.path.join(HERE, "orig", "data")
uw = np.loadtxt(os.path.join(D, "uw_station.csv"), delimiter=",", skiprows=1)
xx = np.arange(0.0, 7950.01, 1.0)
zb0 = np.array([C0.bottom_z(v) for v in xx])
# maalepunkter
stem_x = np.arange(0.0, 851.0, 25.0)
stem_z = np.array([C0.bottom_z(v) for v in stem_x])           # forstevnen slik den er i dag (paa tegningen)
tr = (uw[:, 0] >= 1008.0) & (uw[:, 0] <= 2800.0)
tr_x, tr_z = uw[tr, 0][::6], -uw[tr, 1][::6]                  # sporet forfot/kanobunn
keel_x = np.arange(3200.0, 5701.0, 100.0)
keel_z = np.array([C0.bottom_z(v) for v in keel_x])           # skjult bak kjolen: som i dag
aft_x = np.arange(5800.0, 7951.0, 50.0)
aft_z = np.array([C0.bottom_z(v) for v in aft_x])             # akter: som i dag (sporet er propell/ror)
def run(nm, KN, wk=0.3, wa=1.0, ws=1.0, wt=1.0, sign=1):
    x = np.r_[stem_x, tr_x, keel_x, aft_x]; z = np.r_[stem_z, tr_z, keel_z, aft_z]
    w = np.r_[np.full(len(stem_x), ws), np.full(len(tr_x), wt), np.full(len(keel_x), wk), np.full(len(aft_x), wa)]
    t = L.knots(0.0, 7950.0, KN)
    xr = 0.5 * (P.KEEL_LE_ROOT + P.KEEL_TE_ROOT)
    s = L.fit_shape(x, z, t, w, sign=sign, A=L.basis([xr], t), b=[C0.bottom_z(xr)])
    zz = s(xx); k = L.curvature(s, xx)
    rs = s(stem_x) - stem_z; rt = s(tr_x) - tr_z; rk = s(keel_x) - keel_z; ra = s(aft_x) - aft_z
    trall = (uw[:, 0] >= 1008.0) & (uw[:, 0] <= 2800.0)
    rta = s(uw[trall, 0]) + uw[trall, 1]
    i0 = np.argmin(np.abs(zz[800:1200])) + 800
    print(f"{nm:10s} stem {np.abs(rs).max():5.1f} trace(all pts) {np.abs(rta).max():5.1f} keel {np.abs(rk).max():5.1f} aft {np.abs(ra).max():5.1f} | DWL-kryss x={xx[i0]:.0f} | inflections {len(L.sign_changes(xx, k, 1e-9))}")
    return s
V = {}
V["a"] = run("a", [200, 400, 600, 800, 950, 1100, 1300, 1550, 1850, 2200, 2600, 3000, 3500, 4100, 4700, 5300, 5900, 6500, 7000, 7400, 7700])
V["b"] = run("b", [300, 600, 850, 1050, 1300, 1600, 2000, 2400, 2800, 3300, 4000, 4700, 5400, 6000, 6600, 7100, 7500, 7800])
V["c"] = run("c", [300, 600, 850, 1050, 1300, 1600, 2000, 2400, 2800, 3300, 4000, 4700, 5400, 6000, 6600, 7100, 7500, 7800], sign=0)
V["d"] = run("d", [250, 500, 750, 950, 1150, 1400, 1700, 2100, 2500, 2900, 3400, 4000, 4700, 5400, 6000, 6600, 7100, 7500, 7800])
np.save(os.path.join(HERE, "p5_cases.npy"), {k: (v.t, v.c) for k, v in V.items()}, allow_pickle=True)
fig, ax = plt.subplots(3, 1, figsize=(15, 12))
ax[0].plot(uw[:, 0], -uw[:, 1], ".", color="#bbb", ms=1, label="uw_station.csv")
ax[0].plot(xx, zb0, "k-", lw=0.8, label="orig bottom_z")
ax[1].plot(uw[:, 0], -uw[:, 1], ".", color="#bbb", ms=1)
ax[1].plot(xx, zb0, "k-", lw=0.8)
for nm, s in V.items():
    ax[0].plot(xx, s(xx), lw=1, label=nm); ax[1].plot(xx, s(xx), lw=1)
    ax[2].plot(xx, L.curvature(s, xx) * 1000, lw=1, label=nm)
k0 = np.gradient(np.gradient(zb0, xx), xx) / (1 + np.gradient(zb0, xx) ** 2) ** 1.5 * 1000
ax[2].plot(xx, np.clip(k0, -3, 3), "k-", lw=0.5, alpha=0.5, label="orig")
ax[0].set_ylim(-700, 1300); ax[0].legend(fontsize=7); ax[0].grid()
ax[1].set_xlim(600, 3300); ax[1].set_ylim(-550, 300); ax[1].grid()
ax[2].set_ylim(-0.5, 2.5); ax[2].grid(); ax[2].legend(fontsize=7)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "p5_bottom.png"), dpi=80)
