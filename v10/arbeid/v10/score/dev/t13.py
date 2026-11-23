import sys; sys.path.insert(0, "..")
import numpy as np, score as S
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
V = np.load("V_fine.npy"); F = np.load("F_fine.npy")
slx = S.Slicer(V, F, 0, 10.0)
fig, axs = plt.subplots(1, 3, figsize=(15, 6))
for ax, x in zip(axs, [3550.0, 1450.0, 2500.0]):
    sec = slx.section(x)
    for a, b in zip(sec["P0"], sec["P1"]):
        ax.plot([a[1], b[1]], [a[2], b[2]], 'k-', lw=0.7)
    hb = S.hb_meas(x); zs = S.sheer_meas(x)
    ax.set_xlim(hb - 160, hb + 40); ax.set_ylim(zs - 260, zs + 40); ax.set_aspect('equal'); ax.grid(); ax.set_title(f"x={x}: stanchion hole section")
fig.savefig("hole_sections.png", dpi=80)
