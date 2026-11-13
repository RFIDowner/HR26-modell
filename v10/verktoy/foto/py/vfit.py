"""Vertical relation Enderlein (z_E) vs brochure/model frame (z_B): fit z_E = k z_B + d."""
import sys; sys.path.insert(0, '.')
import numpy as np
import common as c
from prof_cmp import u_z, e_z, E
C, P = c.C, c.P
rows = []
def add(tag, x, zb, ze):
    if np.isfinite(zb) and np.isfinite(ze):
        rows.append((tag, x, zb, ze))
for x in np.arange(1000, 2801, 100):
    add("cb_fwd", x, u_z(x), e_z(x))
for x in [5900, 6000, 6100, 6600, 6700, 6800, 6900]:
    add("cb_aft", x, u_z(x), e_z(x))
kb = c.eline("hull_keel_bottom")
for x in np.arange(4900, 5601, 100):
    m = np.abs(kb[:, 0] - x) < 15
    add("keel_bot", x, u_z(x), kb[m, 1].mean())
st = c.eline("strake_line")
for x in np.arange(800, 3001, 200):
    m = np.abs(st[:, 0] - x) < 20
    if m.any():
        add("strake", x, C.strake_z(x), float(np.median(st[m, 1])))
sh = c.eline("sheer_line")
for x in np.arange(3250, 3800, 100):
    m = np.abs(sh[:, 0] - x) < 20
    if m.any():
        add("sheer", x, C.sheer_z(x), float(np.median(sh[m, 1])))
R = np.array([(r[1], r[2], r[3]) for r in rows])
tags = np.array([r[0] for r in rows])
A = np.c_[R[:, 1], np.ones(len(R))]
for name, sel in [("all", np.ones(len(R), bool)), ("no keel", tags != "keel_bot"), ("no strake/sheer", ~np.isin(tags, ["strake", "sheer"]))]:
    k, d = np.linalg.lstsq(A[sel], R[sel, 2], rcond=None)[0]
    res = R[:, 2] - (k * R[:, 1] + d)
    print(f"{name:16s} k={k:.4f} d={d:6.1f}  rms(sel)={np.sqrt(np.mean(res[sel]**2)):.1f}")
    for t in ["cb_fwd", "cb_aft", "keel_bot", "strake", "sheer"]:
        m = tags == t
        print(f"     {t:9s} n={m.sum():2d} mean res {res[m].mean():6.1f} rms {np.sqrt(np.mean(res[m]**2)):5.1f}")
# pure datum (k=1)
for t in ["cb_fwd", "cb_aft", "keel_bot", "strake", "sheer"]:
    m = tags == t
    print(f"datum z_E - z_B  {t:9s} mean {np.mean(R[m,2]-R[m,1]):6.1f} sd {np.std(R[m,2]-R[m,1]):5.1f}")
