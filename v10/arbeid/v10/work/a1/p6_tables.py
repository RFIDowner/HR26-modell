import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "orig")); sys.path.insert(0, HERE)
from hr26 import curves as C0, params as P
from scipy.interpolate import CubicSpline, PchipInterpolator
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
def check(name, pairs, scale_x, scale_y):
    a = np.array(pairs); t = np.linspace(a[0, 0], a[-1, 0], 4001)
    cs = CubicSpline(a[:, 0], a[:, 1], bc_type="natural"); pc = PchipInterpolator(a[:, 0], a[:, 1])
    for nm, f in (("natural", cs), ("pchip", pc)):
        y = f(t)
        # overshoot: utenfor [min,max] av naboene i hvert intervall
        ov = 0.0
        for (t0, y0), (t1, y1) in zip(a[:-1], a[1:]):
            s = (t >= t0) & (t <= t1)
            ov = max(ov, (y[s] - max(y0, y1)).max(), (min(y0, y1) - y[s]).max())
        d1 = np.gradient(y, t * scale_x) * scale_y; d2 = np.gradient(d1, t * scale_x)
        k = d2 / (1 + d1 ** 2) ** 1.5 * 1000
        sc = np.nonzero(np.diff(np.sign(k[np.abs(k) > 1e-4])))[0]
        print(f"{name:16s} {nm:8s} max {y.max():.4f} overshoot {ov:.4f}  curvature range {k.min():+.2f}..{k.max():+.2f} 1/m  sign changes {len(sc)}")
    return cs, pc
wp = P.WATERPLANE
BW = C0._BW_MAX
cs, pc = check("WATERPLANE", wp, P.LWL, BW)
check("SECTION_FULLNESS", P.SECTION_FULLNESS, P.LOA, 1000.0)
# glattet akterdel: 1 - c*((t-t0)/(te-t0))^p
t0, te, ye = 0.75, 1.015, 0.40
for p in (3.0, 3.5, 4.16):
    f = lambda t: 1 - (1 - ye) * ((t - t0) / (te - t0)) ** p
    print(f"p={p}: " + ", ".join(f"{t:.3f}:{f(t):.3f}" for t in (0.80, 0.85, 0.90, 0.93, 0.95, 1.0, 1.015)))
t = np.linspace(0.6, 1.015, 500)
fig, ax = plt.subplots(2, 1, figsize=(12, 8))
a = np.array(wp)
ax[0].plot(a[:, 0], a[:, 1], "ko-", lw=0.6, label="tabell (np.interp)")
ax[0].plot(t, cs(t), label="natural cubic"); ax[0].plot(t, pc(t), label="pchip")
for p in (3.0, 3.5, 4.16):
    ax[0].plot(t[t >= t0], 1 - (1 - ye) * ((t[t >= t0] - t0) / (te - t0)) ** p, "--", label=f"potens p={p}")
ax[0].set_xlim(0.6, 1.02); ax[0].grid(); ax[0].legend()
ax[1].plot(t, np.gradient(cs(t), t), label="natural d/dt"); ax[1].plot(t, np.gradient(pc(t), t), label="pchip d/dt"); ax[1].grid(); ax[1].legend()
fig.savefig(os.path.join(HERE, "p6_waterplane.png"), dpi=80)
