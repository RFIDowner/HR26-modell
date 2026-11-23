"""Zoomed keel/hull cross-sections for a few x and several KEEL_FILLET values.
usage: python keel_xsec_zoom.py <stage_dir> <tag> 90,45,0
"""
import sys
STAGE, TAG, VALS = sys.argv[1], sys.argv[2], [float(v) for v in sys.argv[3].split(",")]
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/"
sys.path.insert(0, STAGE)
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from hr26 import params as P, curves as C, appendages as AP

XS = [3600, 4600, 5000, 5300]
fig, axs = plt.subplots(len(VALS), len(XS), figsize=(3.3 * len(XS), 2.6 * len(VALS)), sharey=True, sharex=True)
axs = np.atleast_2d(axs)
for i, kf in enumerate(VALS):
    P.KEEL_FILLET = kf
    k = AP.keel()
    for j, x in enumerate(XS):
        ax = axs[i, j]
        sl = k.intersect(cq.Workplane("YZ").workplane(offset=x).rect(4000, 4000).extrude(0.3))
        segs = []
        for e in sl.edges().vals():
            p = [e.positionAt(t) for t in np.linspace(0, 1, 40)]
            if all(abs(q.x - x) < 0.01 for q in p):
                segs.append(np.array([(q.y, q.z) for q in p]))
        sec = np.asarray(C.section(float(x), 200), dtype=float)
        ax.fill_between(sec[:, 0], sec[:, 1], -150, color="0.85")
        ax.fill_between(-sec[:, 0], sec[:, 1], -150, color="0.85")
        ax.plot(sec[:, 0], sec[:, 1], "k-", lw=0.8); ax.plot(-sec[:, 0], sec[:, 1], "k-", lw=0.8)
        for s in segs:
            ax.plot(s[:, 0], s[:, 1], "-", color="tab:red", lw=0.9)
        ax.set_xlim(-360, 360); ax.set_ylim(-640, -230)
        ax.set_aspect("equal"); ax.grid(alpha=0.3)
        ax.set_title(f"x={x}  KEEL_FILLET={kf:.0f}", fontsize=8)
fig.suptitle(f"{TAG}: hull section (grey, solid) and keel slice (red), full-scale mm", fontsize=9)
fig.tight_layout()
fig.savefig(OUT + f"img/keel_zoom_{TAG}.png", dpi=90)
print("ok")
