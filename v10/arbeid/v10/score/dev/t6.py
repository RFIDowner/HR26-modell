import sys; sys.path.insert(0, "..")
import numpy as np, score as S
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
V = np.load("V_fine.npy"); F = np.load("F_fine.npy")
fn, *_ = S.face_geom(V, F)
slx = S.Slicer(V, F, 0, 10.0)
fig, axs = plt.subplots(1, 6, figsize=(22, 6))
for ax, x in zip(axs, [300., 600., 1050., 3000., 6000., 7650.]):
    sec = slx.section(x); sec["n"] = fn[sec["f"]]
    y0, z0, y1, z1 = S._seg_yz(sec, 1)
    for a, b, c, d in zip(y0, z0, y1, z1):
        ax.plot([a, c], [b, d], 'k-', lw=0.5)
    zk = S.strake_meas(x); hb = S.hb_meas(x)
    ax.axhline(zk, color='r', lw=0.5)
    ax.set_xlim(hb - 250, hb + 80); ax.set_ylim(zk - 250, zk + 250); ax.set_aspect('equal'); ax.set_title(f"x={x}")
    ax.grid()
fig.savefig("strake_sections.png", dpi=70)
