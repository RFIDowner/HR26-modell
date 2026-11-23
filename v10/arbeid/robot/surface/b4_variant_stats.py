import sys, os
import numpy as np
from scipy.spatial import cKDTree
SC = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface"
sys.path.insert(0, SC)
from common import load_raw, weld, face_normals, edges_adjacency
def load(path):
    T = load_raw(path); V, F = weld(T); fn, area = face_normals(V, F); return V, F, fn, area
def mk(path):
    V, F, fn, a = load(path); c = V[F].mean(1); return dict(V=V, F=F, fn=fn, a=a, c=c, tree=cKDTree(c))
def dist(ref, P):
    dd, ii = ref["tree"].query(P, k=6)
    pl = np.einsum("ijk,ijk->ij", P[:, None, :] - ref["c"][ii], ref["fn"][ii])
    return pl[np.arange(len(P)), np.argmin(dd, axis=1)]
ref_var = mk(SC + "/loft/variant_abs0.002.stl")
ref_org = mk(SC + "/loft/loft_t0.002_a0.02.stl")
for path, tag in (("variant_rel0.018.stl", "VARIANT relative 0.018 (shipped call)"), ("variant_abs0.005.stl", "VARIANT absolute 0.005 mm")):
    V, F, fn, area = load(SC + "/loft/" + path); c = V[F].mean(1)
    side = (np.abs(fn[:, 2]) < 0.9) & (c[:, 0] < 7700 / 30) & (c[:, 0] > 15)
    E, f1, f2, cnt = edges_adjacency(F)
    both = side[f1] & side[f2]
    dih = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", fn[f1], fn[f2]), -1, 1)))[both]
    lmax = np.max(np.stack([np.linalg.norm(V[F[:, i]] - V[F[:, (i + 1) % 3]], axis=1) for i in range(3)], 1), 1)
    asp = lmax / np.maximum(2 * area / np.maximum(lmax, 1e-12), 1e-12)
    d = np.abs(dist(ref_var, c[side]))
    print(f"{tag:38s} tri {len(F):7d} ({os.path.getsize(SC + '/loft/' + path)/1e6:5.1f} MB) | longest edge p50 {np.median(lmax[side]):5.2f} max {lmax[side].max():5.1f} mm, aspect>20 {np.mean(asp[side]>20)*100:4.1f}% | "
          f"dihedral p50 {np.percentile(dih,50):.2f} p99 {np.percentile(dih,99):5.2f}, >2deg {np.mean(dih>2)*100:4.1f}% >5deg {np.mean(dih>5)*100:5.2f}% | chordal p95 {np.percentile(d,95):.4f} max {d.max():.3f} mm")
# shape change: variant surface vs original surface (both fine), side region, in full-scale mm
Vv, Fv = ref_var["V"], ref_var["F"]; cv = ref_var["c"]; fnv = ref_var["fn"]
side = (np.abs(fnv[:, 2]) < 0.9) & (cv[:, 0] < 7700 / 30) & (cv[:, 0] > 15) & (cv[:, 1] > 0)
d = dist(ref_org, cv[side]) * 30.0
x = cv[side, 0] * 30.0; z = cv[side, 2] * 30.0
print(f"\nvariant minus original surface (full-scale mm, starboard side): p50 |d| {np.median(np.abs(d)):.2f}, p95 {np.percentile(np.abs(d),95):.2f}, max {np.abs(d).max():.1f}")
for x0 in range(0, 8000, 1000):
    m = (x >= x0) & (x < x0 + 1000)
    if m.sum():
        i = np.argmax(np.abs(d[m]))
        print(f"   x {x0:4d}-{x0+1000:4d}: p95 |d| {np.percentile(np.abs(d[m]),95):6.2f}  max {np.abs(d[m]).max():6.1f} at z={z[m][i]:.0f}")
for zb in ((-600, -200), (-200, -30), (-30, 30), (30, 300), (300, 1300)):
    m = (z >= zb[0]) & (z < zb[1]) & (x > 1500) & (x < 7000)
    print(f"   z {zb}: x1500-7000 p95 |d| {np.percentile(np.abs(d[m]),95):6.2f} max {np.abs(d[m]).max():6.1f}")
