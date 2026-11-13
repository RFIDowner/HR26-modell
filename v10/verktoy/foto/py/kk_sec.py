"""kk_: modellens tverrsnitt (STL) ved valgte x, styrbord halvdel, z > 700.
Ut: scratchpad/kk_sec.png og tallene for karm/dekk."""
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import common as c
import geo9374 as G
G.use_model(None)
import kk_lib as L
from hr26 import deckhouse as D
P, C = c.P, c.C
SP = sys.argv[1]
V, F = L.model_mesh()
m = trimesh.Trimesh(V, F, process=False)
xs = [float(a) for a in sys.argv[2:]] or [5000, 5600, 5800, 6200, 6600, 6900, 7300, 7700]
fig, axs = plt.subplots(len(xs), 1, figsize=(9, 2.6 * len(xs)))
for ax, x in zip(np.atleast_1d(axs), xs):
    sec = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
    if sec is None:
        continue
    for ent in sec.discrete:
        p = np.asarray(ent)
        ax.plot(p[:, 1], p[:, 2], "k-", lw=0.8)
    hb = C.deck_half_breadth(x)
    ax.plot([hb], [C.sheer_z(x)], "co")
    if x < P.COAMING_X1:
        ax.plot([D.coaming_half_width(x)], [D.coaming_top_z(x)], "yo")
    ax.set_xlim(300, 1400)
    ax.set_ylim(700, 1450)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3)
    ax.set_title("x = %.0f  sheer %.0f  hb %.0f" % (x, C.sheer_z(x), hb), fontsize=8)
plt.tight_layout()
plt.savefig(SP + "/kk_sec.png", dpi=80)
