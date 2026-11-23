"""Step 1b: crease map (x vs z, starboard) and crease classification."""
import sys
import numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface")
from common import *
sys.path.insert(0, REPO)
from hr26 import curves as C, params as P, hull as H
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

D = np.load(OUT + "/a1.npz")
Vf, F, fn, cls, E, f1, f2, dih, asp = (D[k] for k in ("Vf", "F", "fn", "cls", "E", "f1", "f2", "dih", "asp"))

# loft stations exactly as hull_solid(40, 26) makes them
xs = C.stations(40)
xs = [x for x in xs if 6.0 < x < P.LOA - 4.0]
xs = sorted(set([4.0] + xs + list(H.STERN_STATIONS) + [P.LOA - 2.0]))
xs = np.array([x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 8.0])
print("loft stations:", len(xs), " spacing min/max", np.diff(xs).min().round(1), np.diff(xs).max().round(1))
np.save(OUT + "/stations.npy", xs)

A = Vf[E[:, 0]]; B = Vf[E[:, 1]]
mid = 0.5 * (A + B); dv = B - A
c1, c2 = cls[f1], cls[f2]
hull_e = np.isin(c1, (1, 3)) & np.isin(c2, (1, 3))
stb = mid[:, 1] > -1.0
near_st = np.min(np.abs(mid[:, 0][:, None] - xs[None, :]), axis=1)
in_station_plane = (np.abs(dv[:, 0]) < 1.0) & (near_st < 1.5)
along = np.abs(dv[:, 0]) > 3 * np.hypot(dv[:, 1], dv[:, 2])
girth = np.abs(dv[:, 0]) < 0.33 * np.hypot(dv[:, 1], dv[:, 2])
sk = np.array([C.strake_z(x) for x in mid[:, 0]]); sh = np.array([C.sheer_z(x) for x in mid[:, 0]])

for th in (2, 5, 10):
    m = hull_e & (dih > th)
    print(f"\nhull-exterior edges with dihedral > {th} deg: {m.sum()}")
    print(f"   lying in a loft-station plane (|dx|<1 mm, x within 1.5 mm of a station): {np.mean(in_station_plane[m])*100:.1f} %")
    print(f"   oriented along girth (|dx| < 0.33*|dyz|): {np.mean(girth[m])*100:.1f} %   along hull (|dx| > 3*|dyz|): {np.mean(along[m])*100:.1f} %   diagonal: {np.mean(~girth[m] & ~along[m])*100:.1f} %")
    zz = mid[m, 2]
    print(f"   z bands (full mm): <-300 {np.mean(zz<-300)*100:.0f}%  -300..-50 {np.mean((zz>=-300)&(zz<-50))*100:.0f}%  -50..50 (DWL) {np.mean(np.abs(zz)<50)*100:.0f}%  50..strake-60 {np.mean((zz>=50)&(zz<sk[m]-60))*100:.0f}%  near strake {np.mean(np.abs(zz-sk[m])<=60)*100:.0f}%  above strake {np.mean(zz>sk[m]+60)*100:.0f}%")
    xx = mid[m, 0]
    hist, be = np.histogram(xx, bins=np.arange(0, 8001, 500))
    print("   x histogram per 500 mm:", hist.tolist())

# what fraction of all hull-exterior edges lie in station planes, and their dihedral
m = hull_e & in_station_plane
print(f"\nall hull edges in station planes: {m.sum()} of {hull_e.sum()};  median dihedral there {np.median(dih[m]):.2f}  vs elsewhere {np.median(dih[hull_e & ~in_station_plane]):.2f}")
# junction edges
for a, b, nm in ((1, 2, "hull|strake"), (1, 0, "hull|deck/other"), (1, 4, "hull|transom"), (1, 5, "hull|keel"), (1, 3, "hull|window"), (2, 0, "strake|other")):
    mm = ((c1 == a) & (c2 == b)) | ((c1 == b) & (c2 == a))
    if mm.sum():
        print(f"junction {nm:16s}: {mm.sum():5d} edges, dihedral median {np.median(dih[mm]):6.1f}, p90 {np.percentile(dih[mm], 90):6.1f}")

# -------- figure: side view crease map, starboard, hull exterior + strake
fig, ax = plt.subplots(figsize=(16, 6.2), dpi=100)
fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")
ext = np.isin(c1, (1, 2, 3, 4)) | np.isin(c2, (1, 2, 3, 4))
base = stb & ext & (dih <= 2)
ax.add_collection(LineCollection(np.stack([A[base][:, [0, 2]], B[base][:, [0, 2]]], 1), colors="#d9d8d2", linewidths=0.35, zorder=1))
for lo, hi, col, lw, lab in ((2, 5, "#86b6ef", 0.8, "2-5 deg"), (5, 10, "#2a78d6", 1.1, "5-10 deg"), (10, 181, "#104281", 1.6, "> 10 deg")):
    m = stb & ext & (dih > lo) & (dih <= hi)
    ax.add_collection(LineCollection(np.stack([A[m][:, [0, 2]], B[m][:, [0, 2]]], 1), colors=col, linewidths=lw, zorder=3, label=f"edge dihedral {lab} ({m.sum()})"))
for x in xs:
    ax.axvline(x, color="#eb6834", lw=0.5, alpha=0.55, zorder=2)
ax.plot([], [], color="#eb6834", lw=0.8, label="loft stations (hull_solid 40 x 26)")
xx = np.linspace(0, 7950, 400)
ax.plot(xx, [C.strake_z(x) for x in xx], color="#52514e", lw=0.6, ls=":", zorder=4)
ax.plot(xx, [C.sheer_z(x) for x in xx], color="#52514e", lw=0.6, ls="--", zorder=4)
ax.axhline(0, color="#52514e", lw=0.6, ls="-.", zorder=4)
ax.text(60, 15, "DWL", color="#52514e", fontsize=8); ax.text(60, C.sheer_z(60) + 15, "deck edge", color="#52514e", fontsize=8)
ax.text(260, C.strake_z(260) - 60, "strake centre", color="#52514e", fontsize=8)
ax.set_xlim(-50, 8050); ax.set_ylim(-700, 1300)
ax.set_aspect("equal")
ax.set_xlabel("x from bow, full-scale mm"); ax.set_ylabel("z over DWL, full-scale mm")
ax.set_title("01_skrog.stl, starboard hull exterior + strake + transom: creases between adjacent triangles", fontsize=11, loc="left")
ax.legend(loc="lower right", fontsize=8, frameon=False, ncol=2)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(OUT + "/fig1_crease_map.png", dpi=100, facecolor="#fcfcfb")
print("saved fig1")
