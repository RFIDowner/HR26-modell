"""Facet statistics of the Bambu hull topsides (numpy-only parse of untrusted STL; run with python -I).
Scale: Bambu units * 0.3708 = our model mm; * 30 = full-scale mm. x from bow at -404."""
import sys
import numpy as np

FN = sys.argv[1]
with open(FN, "rb") as f:
    f.read(80)
    n = int(np.frombuffer(f.read(4), np.uint32)[0])
    dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec = np.frombuffer(f.read(n * 50), dt, count=n)
tri = rec["v"].astype(np.float64) * 0.3708 * 30.0   # full-scale mm, isotropic
xb0 = -404.0 * 0.3708 * 30.0
tri[..., 0] -= xb0
print("triangles", n, "x range", tri[..., 0].min(), tri[..., 0].max())
V = tri.reshape(-1, 3)
key = np.round(V * 1e3).astype(np.int64)
uk, inv = np.unique(key, axis=0, return_inverse=True)
inv = inv.ravel()
Vu = np.zeros((len(uk), 3)); Vu[inv] = V
T = inv.reshape(-1, 3)
P0, P1, P2 = Vu[T[:, 0]], Vu[T[:, 1]], Vu[T[:, 2]]
N = np.cross(P1 - P0, P2 - P0); A = 0.5 * np.linalg.norm(N, axis=1)
N /= np.where(A > 0, 2 * A, 1)[:, None]
cen = (P0 + P1 + P2) / 3
# outer hull: per 100 mm x-bin, max y of side-facing triangles
side = (np.abs(N[:, 2]) < 0.7) & (N[:, 1] > 0.6) & (cen[:, 1] > 0)
bins = np.arange(0, 8100, 100)
ymax = np.zeros(len(bins))
for i, b in enumerate(bins):
    m = side & (cen[:, 0] >= b) & (cen[:, 0] < b + 100)
    ymax[i] = cen[m, 1].max() if m.any() else 0
ym = np.interp(cen[:, 0], bins + 50, ymax)
top = side & (cen[:, 0] > 1500) & (cen[:, 0] < 6800) & (cen[:, 1] > 0.8 * ym)
idx = np.where(top)[0]
print("z range of selected (full mm, Bambu frame):", cen[idx, 2].min(), cen[idx, 2].max())
E = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
tid = np.tile(np.arange(len(T)), 3)
Es = np.sort(E, axis=1)
o = np.lexsort((Es[:, 1], Es[:, 0])); Es, tid = Es[o], tid[o]
i = np.where(np.all(Es[1:] == Es[:-1], axis=1))[0]
ta, tb = tid[i], tid[i + 1]
sel = np.zeros(len(T), bool); sel[idx] = True
both = sel[ta] & sel[tb]
ang = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", N[ta[both]], N[tb[both]]), -1, 1)))
area = A[idx].sum() / 1e6
ext = np.ptp(Vu[T[idx]][:, :, 0], axis=1)
print(f"Bambu topside (x1500-6800 equiv, y>0.8*ymax, side-facing): {len(idx)} triangles over {area:.2f} m2 = {len(idx)/area:.0f}/m2;"
      f" triangle x-extent median {np.median(ext):.0f} mm, 90% {np.percentile(ext,90):.0f}")
print(f"dihedral between neighbouring facets: median {np.median(ang):.2f}, 90% {np.percentile(ang,90):.2f}, 99% {np.percentile(ang,99):.2f} deg")

# split by height band; z_b = -37.4 (max beam / strake) -> -416 full in this frame
for lo, hi in [(-1100, -700), (-700, -450), (-450, -250), (-250, 400)]:
    m = top & (cen[:, 2] >= lo) & (cen[:, 2] < hi)
    ii = np.where(m)[0]
    if len(ii) < 10:
        print(lo, hi, "few"); continue
    s2 = np.zeros(len(T), bool); s2[ii] = True
    bb = s2[ta] & s2[tb]
    a2 = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", N[ta[bb]], N[tb[bb]]), -1, 1)))
    ar = A[ii].sum() / 1e6
    print(f"  z {lo}..{hi}: {len(ii)} tris, {len(ii)/ar:.0f}/m2, x-ext median {np.median(np.ptp(Vu[T[ii]][:, :, 0], axis=1)):.0f} mm;"
          f" dihedral median {np.median(a2):.2f}, 90% {np.percentile(a2,90):.2f}")
# smoothness at a larger scale: normals averaged over 100 mm patches along a horizontal line at z=-700
m = top & (np.abs(cen[:, 2] + 700) < 40)
ii = np.where(m)[0]
o = np.argsort(cen[ii, 0])
xs = cen[ii, 0][o]; nn = N[ii][o]
heading = np.degrees(np.arctan2(nn[:, 0], nn[:, 1]))
for w in (25, 50, 100, 200):
    bins = np.arange(1500, 6800, w)
    hm = np.array([heading[(xs >= b) & (xs < b + w)].mean() for b in bins if ((xs >= b) & (xs < b + w)).sum() > 0])
    print(f"  normal heading averaged over {w} mm windows at z=-700: step between windows median {np.median(np.abs(np.diff(hm))):.2f}, 90% {np.percentile(np.abs(np.diff(hm)),90):.2f} deg")
