"""Plan-snitt rundt hekken (fullskala) for en eller to STL-er. argv: out.png stl1 [stl2]"""
import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b")
from geo import *
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
out = sys.argv[1]; paths = sys.argv[2:]
zs = (-150, 0, 200, 400, 600, 804, 880, 930)
fig, axs = plt.subplots(2, 4, figsize=(16, 8.5))
cols = ["k", "r"]
for pi, p in enumerate(paths):
    T = full_tris(p)
    for ax, z in zip(axs.ravel(), zs):
        for P in outer_lines(T, 2, z):
            m = (P[:, 0] > 7450)
            if m.sum() < 2: continue
            ax.plot(P[:, 0], P[:, 1], cols[pi] + "-", lw=0.8)
        ax.set_title(f"z = {z}")
        ax.set_xlim(7450, 8000); ax.set_ylim(0, 1000); ax.set_aspect("equal"); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(out, dpi=90)
