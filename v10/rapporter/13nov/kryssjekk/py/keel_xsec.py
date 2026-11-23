"""Keel cross-sections (CAD slice of A.keel()) against the hull section at the
same x, for one patch stage. Reports the exposed keel half-width (keel points
outside the hull) per x, and the height of the widest flare ring (z1) relative
to the hull surface at that half-width.

usage: python keel_xsec.py <stage_dir> <tag>
"""
import sys, json, time
STAGE, TAG = sys.argv[1], sys.argv[2]
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/74d216f8-f70b-497f-9ffe-f65637a9e826/scratchpad/kontroll/kryssjekk/"
sys.path.insert(0, STAGE)
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from hr26 import params as P, curves as C, appendages as AP

t0 = time.time()
k = AP.keel()
kv = k.val()
bb = kv.BoundingBox()
kp = AP._KeelProfile()
print(f"[{TAG}] keel valid {kv.isValid()} vol {kv.Volume()/1e9:.4f} m3 (fast) bbox x {bb.xmin:.0f}..{bb.xmax:.0f} "
      f"y {bb.ymin:.0f}..{bb.ymax:.0f} z {bb.zmin:.0f}..{bb.zmax:.0f}; fillet ends fwd ({kp.fwd[0,0]:.0f},{kp.fwd[0,1]:.0f}) "
      f"aft ({kp.aft[0,0]:.0f},{kp.aft[0,1]:.0f})  {time.time()-t0:.1f}s", flush=True)

XS = [3250, 3400, 3600, 4000, 4600, 5000, 5300, 5500, 5650, 5800, 5880]


def hull_bottom(x):
    sec = np.asarray(C.section(float(x), 160), dtype=float)
    i = int(np.argmax(sec[:, 0]))
    b = sec[: i + 1]
    # keep monotonic in y
    keep = [0]
    for j in range(1, len(b)):
        if b[j, 0] > b[keep[-1], 0]:
            keep.append(j)
    return sec, b[keep]


res = {}
fig, axs = plt.subplots(1, len(XS), figsize=(1.9 * len(XS), 4.0), sharey=True)
for ax, x in zip(axs, XS):
    sl = k.intersect(cq.Workplane("YZ").workplane(offset=x).rect(4000, 4000).extrude(0.3))
    pts = []
    for e in sl.edges().vals():
        for t in np.linspace(0, 1, 60):
            p = e.positionAt(t)
            if abs(p.x - x) < 0.01:
                pts.append((p.y, p.z))
    pts = np.array(pts) if pts else np.zeros((0, 2))
    sec, bot = hull_bottom(x)
    zp = float(C.bottom_z(float(x)))
    ax.plot(sec[:, 0], sec[:, 1], "k-", lw=1)
    ax.plot(-sec[:, 0], sec[:, 1], "k-", lw=1)
    r = dict(bz=round(zp, 1))
    if len(pts):
        ax.plot(pts[:, 0], pts[:, 1], ".", color="tab:red", ms=1.2)
        zh = np.interp(np.abs(pts[:, 0]), bot[:, 0], bot[:, 1])
        out = pts[pts[:, 1] < zh - 1.0]
        if len(out):
            # exposed half-width as a function of height: is it monotonic (no ledge)?
            zz = np.round(out[:, 1] / 10.0) * 10.0
            prof = {}
            for zv, yv in zip(zz, np.abs(out[:, 0])):
                prof[zv] = max(prof.get(zv, 0.0), yv)
            zs = sorted(prof)              # bottom -> up
            hw = np.array([prof[z] for z in zs])
            # a ledge: half-width decreasing going up at the top of the exposed part
            imax = int(np.argmax(hw))
            r.update(
                exposed_max_hw=round(float(hw.max()), 1),
                z_at_max=round(float(zs[imax]), 1),
                exposed_top_z=round(float(max(zs)), 1),
                hw_at_top=round(float(hw[-1]), 1),
                ledge=bool(hw.max() - hw[-1] > 15.0),
            )
            ax.plot(out[:, 0], out[:, 1], ".", color="tab:blue", ms=1.5)
    res[x] = r
    ax.set_xlim(-420, 420)
    ax.set_ylim(-760, -200)
    ax.set_title(f"x={x}", fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_aspect("equal")
fig.suptitle(f"{TAG}: keel slices (red; blue = outside the hull) vs hull section (black), full-scale mm", fontsize=9)
fig.tight_layout()
fig.savefig(OUT + f"img/keel_xsec_{TAG}.png", dpi=95)
json.dump(res, open(OUT + f"out/keel_xsec_{TAG}.json", "w"), indent=1)
for x, r in res.items():
    print(x, r)
print(f"done {time.time()-t0:.1f}s")
