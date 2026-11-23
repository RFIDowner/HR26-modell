"""Sammenlign naken loft: plan-snitt og senterlinjeprofil rundt hekken. argv: old.stl new.stl out.png"""
import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b")
from common import load_raw
from elib import section, chain
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
def load_full(p):
    return load_raw(p).astype(np.float64) * 30.0   # already in full-scale frame /30
old, new, out = sys.argv[1], sys.argv[2], sys.argv[3]
To, Tn = load_full(old), load_full(new)
zs = (-200, -100, 0, 200, 400, 600, 804, 900, 940, 960)
fig, axs = plt.subplots(2, 6, figsize=(21, 8))
for ax, z in zip(axs.ravel(), zs):
    for T, col in ((To, "k"), (Tn, "r")):
        for L in chain(section(T, 2, z), tol=1e-4):
            ax.plot(L[:, 0], L[:, 1], col + "-", lw=0.9)
    ax.set_xlim(7550, 8000); ax.set_ylim(0, 900); ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_title(f"z={z}")
ax = axs.ravel()[-2]
for T, col in ((To, "k"), (Tn, "r")):
    for L in chain(section(T, 1, 0.0), tol=1e-4):
        ax.plot(L[:, 0], L[:, 2], col + "-", lw=0.9)
ax.set_xlim(7500, 8000); ax.set_ylim(-400, 1100); ax.set_title("senterlinje y=0"); ax.grid(alpha=.3)
ax = axs.ravel()[-1]
for T, col in ((To, "k"), (Tn, "r")):
    for L in chain(section(T, 1, 600.0), tol=1e-4):
        ax.plot(L[:, 0], L[:, 2], col + "-", lw=0.9)
ax.set_xlim(7500, 8000); ax.set_ylim(-400, 1100); ax.set_title("y=600"); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(out, dpi=75)
