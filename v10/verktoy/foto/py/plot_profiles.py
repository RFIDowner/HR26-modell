from common import *
from hr26 import params as P, curves as C
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, csv
E = ender()["profile"]
ux, ud = [], []
for r in csv.DictReader(open(REPO + "/data/uw_station.csv")):
    ux.append(float(r["x_from_bow_mm"])); ud.append(-float(r["depth_below_DWL_mm"]))
fig, ax = plt.subplots(figsize=(16, 6))
ax.plot(ux, ud, "k.", ms=1.5, label="brochure trace uw_station.csv")
for k in ["hull_aft_bottom", "hull_te_fillet", "hull_te", "hull_keel_bottom", "hull_keel_le", "hull_fwd_bottom", "hull_stem", "transom", "rudder_le_upper"]:
    a = np.array(E[k]["xz"]); ax.plot(a[:, 0], a[:, 1], ".", ms=2, label="E " + k)
xs = np.linspace(0, 7950, 800)
ax.plot(xs, [C.bottom_z(x) for x in xs], "r-", lw=1, label="model bottom_z")
zz = np.linspace(-450, 960, 50); ax.plot([C.transom_x(z) for z in zz], zz, "r-", lw=1)
h = np.array(P.CANOE_BOTTOM_HIDDEN); ax.plot(h[:, 0], h[:, 1], "r+", label="CANOE_BOTTOM_HIDDEN")
ax.axhline(0, color="b", lw=0.5); ax.set_xlim(-100, 8300); ax.set_ylim(-1450, 1250); ax.set_aspect("equal"); ax.grid(lw=0.3)
ax.legend(fontsize=6, ncol=3); fig.tight_layout(); fig.savefig(W + "/img/profiles_raw.png", dpi=100)
