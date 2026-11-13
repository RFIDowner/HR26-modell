"""Kontrollbilde for forkroppen (trinn 5): vannlinjer over hele lengden og
spant forut, dagens modell (stiplet) mot en tilpasning
(out/opt_forkropp_<tag>.json).

Kjoeres fra denne mappa: python glatt_forkropp.py TAG UT.png
"""
import json
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import common as c, hjerte as Hj
import opt_forkropp as OF

tag, out = sys.argv[1], sys.argv[2]
fit = json.load(open(c.W + "/out/opt_forkropp_%s.json" % tag))
over = {k: [tuple(p) for p in v] for k, v in fit["params"].items()}
XSEC = (1000.0, 1600.0, 2200.0, 2800.0, 3400.0, 4000.0, 4600.0)
fig, ax = plt.subplots(1, 2, figsize=(16, 6.5), gridspec_kw=dict(width_ratios=[1.6, 1]))
for lab, ov, ls in (("i dag", {}, "--"), (tag, over, "-")):
    C = Hj.apply(ov)
    Y = OF.waterlines(C)
    for i, z in enumerate(OF.ZW):
        ax[0].plot(OF.XG, Y[i], ls, color=plt.cm.viridis(i / (len(OF.ZW) - 1)), lw=1.3,
                   label=f"z {z:+.0f}" if ls == "-" else None)
    for j, x in enumerate(XSEC):
        p = np.array(C.section(float(x), 200))
        col = plt.cm.plasma(j / len(XSEC))
        ax[1].plot(p[:, 0], p[:, 1], ls, color=col, lw=1.3, label=f"x {x:.0f}" if ls == "-" else None)
        ax[1].plot(-p[:, 0], p[:, 1], ls, color=col, lw=1.3)
ax[0].set_title("Vannlinjer (stiplet: i dag, hel: %s)" % tag)
ax[0].set_xlabel("x (mm fra baugen)"); ax[0].set_ylabel("halvbredde (mm)")
ax[0].legend(fontsize=8, ncol=2); ax[0].grid(alpha=0.3)
ax[1].set_title("Spant forut (stiplet: i dag)"); ax[1].set_aspect("equal"); ax[1].grid(alpha=0.3)
ax[1].axhline(0, color="k", lw=0.5); ax[1].set_ylim(-500, 700); ax[1].legend(fontsize=7)
fig.tight_layout(); fig.savefig(out, dpi=85)
print(out)
