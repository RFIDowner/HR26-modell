"""Step 1: weld, classify, mesh statistics and dihedral angles for 01_skrog.stl."""
import sys, math, time
import numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface")
from common import *
sys.path.insert(0, REPO)
from hr26 import curves as C, params as P

t0 = time.time()
T32 = load_raw(OURS)
print("triangles", len(T32))
V0, F = weld(T32)
Vq, Fq = weld(T32, q=1e-4)
print("unique verts exact", len(V0), " quantized 1e-4:", len(Vq))
# degenerate faces
deg = (F[:, 0] == F[:, 1]) | (F[:, 1] == F[:, 2]) | (F[:, 0] == F[:, 2])
print("degenerate (repeated vertex) faces", deg.sum())

ang = min(np.arange(30, 60.01, 0.25), key=lambda d: np.ptp(rotz(V0, -d)[:, 1]))
print("best un-rotation", ang)
V = rotz(V0, -45.0)
V[:, 1] -= 0.5 * (V[:, 1].max() + V[:, 1].min())
# bow at min x?  check width near both ends
xmin, xmax = V[:, 0].min(), V[:, 0].max()
nb = V[V[:, 0] < xmin + 10]; ns = V[V[:, 0] > xmax - 10]
print("x range", xmin, xmax, "len", xmax - xmin, " width near minx", np.ptp(nb[:, 1]), " near maxx", np.ptp(ns[:, 1]))
print("z range", V[:, 2].min(), V[:, 2].max())

fn, area = face_normals(V, F)
lab = components(len(V), F)
ul, cnt = np.unique(lab, return_counts=True)
order = np.argsort(-cnt)
print("components:", len(ul), " sizes:", cnt[order][:12])
outer_lab = ul[order[0]]
# confirm outer by bbox
for k in order[:6]:
    m = lab == ul[k]
    vv = V[F[m].ravel()]
    vol = np.sum(np.einsum("ij,ij->i", V[F[m, 0]], np.cross(V[F[m, 1]], V[F[m, 2]]))) / 6
    print(f"  comp {ul[k]} faces {cnt[k]} xr {vv[:,0].min():.1f}..{vv[:,0].max():.1f} zr {vv[:,2].min():.1f}..{vv[:,2].max():.1f} signed vol {vol:.0f}")

Vf = to_full(V, xmin)
print("full-scale x range", Vf[:, 0].min(), Vf[:, 0].max(), " z range", Vf[:, 2].min(), Vf[:, 2].max())

# ---------------- analytic grid y_a(x,z), outward normal (ny,nz) in section plane
xg = np.arange(0.0, 7960.0, 10.0)
zg = np.arange(-600.0, 1260.0, 5.0)
YA = np.full((len(xg), len(zg)), np.nan); NY = np.zeros_like(YA); NZ = np.zeros_like(YA)
for i, x in enumerate(xg):
    sec = np.array(C.section(max(x, 4.0), 240))
    y, z = sec[:, 0], sec[:, 1]
    o = np.argsort(z); y, z = y[o], z[o]
    inr = (zg >= z[0]) & (zg <= z[-1])
    YA[i, inr] = np.interp(zg[inr], z, y)
    ty = np.gradient(y); tz = np.gradient(z); L = np.hypot(ty, tz) + 1e-12
    NY[i, inr] = np.interp(zg[inr], z, tz / L); NZ[i, inr] = np.interp(zg[inr], z, -ty / L)
sheer = np.array([C.sheer_z(x) for x in xg]); strk = np.array([C.strake_z(x) for x in xg])
bot = np.array([C.bottom_z(max(x, 4.0)) for x in xg])


def grid(G, x, z):
    i = np.clip(np.round(x / 10.0).astype(int), 0, len(xg) - 1)
    j = np.clip(np.round((z + 600.0) / 5.0).astype(int), 0, len(zg) - 1)
    return G[i, j]


def line(arr, x):
    return np.interp(x, xg, arr)


c = Vf[F].mean(1)
cx, cy, cz = c[:, 0], c[:, 1], c[:, 2]
ya = grid(YA, cx, cz)
d = np.abs(cy) - ya
dot = fn[:, 1] * np.sign(cy) * grid(NY, cx, cz) + fn[:, 2] * grid(NZ, cx, cz)
sh = line(sheer, cx); sk = line(strk, cx); bz = line(bot, cx)
tx = np.array([C.transom_x(z, y) for z, y in zip(cz, cy)])
outer = lab == outer_lab

cls = np.zeros(len(F), int)                                  # 0 other (deck, roof, keel, fittings)
cls[~outer] = 6                                              # interior cavities
in_strake_band = np.abs(cz - sk) < (0.5 * P.STRAKE_H + 12)
hullside = outer & (np.abs(d) < 22) & (dot > 0.5) & (cz < sh - 12) & (cx < tx - 12) & ~np.isnan(ya)
strake = outer & in_strake_band & (d > 8) & (d < 75) & (cx > 150) & (cx < tx + 80)
window = hullside & (cx > P.WIN_X0 - 40) & (cx < P.WIN_X1 + 40) & (cz > sk + 40) & (d < -2)
transom = outer & (np.abs(cx - tx) < 15) & (fn[:, 0] > 0.6)
keel = outer & (cz < bz - 15) & (np.abs(cy) < 250)
cls[hullside] = 1
cls[strake & ~hullside] = 2
cls[strake & hullside & (d > 8)] = 2
cls[window] = 3
cls[transom & (cls == 0)] = 4
cls[keel & (cls == 0)] = 5
names = {0: "other(deck/roof/cockpit/fittings)", 1: "hull exterior (side+bottom)", 2: "rubbing strake", 3: "window recess", 4: "transom", 5: "keel", 6: "interior cavities"}
for k in range(7):
    m = cls == k
    print(f"class {k} {names[k]:<34s} faces {m.sum():7d}  area {area[m].sum():9.0f} mm2")

# ------------------ edges, dihedral
E, f1, f2, counts = edges_adjacency(F)
print("edges: total unique", len(counts), " manifold", (counts == 2).sum(), " boundary(1)", (counts == 1).sum(), " >2:", (counts > 2).sum())
cosang = np.clip(np.einsum("ij,ij->i", fn[f1], fn[f2]), -1, 1)
dih = np.degrees(np.arccos(cosang))

# ------------------ triangle quality per class
el = np.stack([np.linalg.norm(V[F[:, 1]] - V[F[:, 0]], axis=1), np.linalg.norm(V[F[:, 2]] - V[F[:, 1]], axis=1), np.linalg.norm(V[F[:, 0]] - V[F[:, 2]], axis=1)], 1)
lmax = el.max(1); lmin = el.min(1)
alt = 2 * area / np.maximum(lmax, 1e-12)        # altitude onto longest edge
asp = lmax / np.maximum(alt, 1e-12)
for k in (1, 2):
    m = cls == k
    print(f"\n== {names[k]}: {m.sum()} triangles")
    print("   edge length (model mm) min/p5/median/p95/max: " + " ".join(f"{v:.3f}" for v in np.percentile(el[m].ravel(), [0, 5, 50, 95, 100])))
    print("   longest edge p50/p95/max:", " ".join(f"{v:.2f}" for v in np.percentile(lmax[m], [50, 95, 100])))
    print("   aspect (longest edge / altitude) p50/p90/p99:", " ".join(f"{v:.1f}" for v in np.percentile(asp[m], [50, 90, 99])))
    for th in (5, 10, 20, 50):
        print(f"   share aspect > {th}: {np.mean(asp[m] > th) * 100:.1f} %  (area share {area[m][asp[m] > th].sum() / area[m].sum() * 100:.1f} %)")
    ee = (cls[f1] == k) & (cls[f2] == k)
    dd = dih[ee]
    print(f"   interior edges {ee.sum()}: dihedral p50 {np.percentile(dd,50):.2f}  p90 {np.percentile(dd,90):.2f}  p99 {np.percentile(dd,99):.2f}  max {dd.max():.1f} deg")
    for th in (1, 2, 5, 10):
        print(f"     share > {th:2d} deg: {np.mean(dd > th) * 100:.2f} %  ({(dd > th).sum()} edges)")

np.savez_compressed(OUT + "/a1.npz", V=V, Vf=Vf, F=F, fn=fn, area=area, cls=cls, E=E, f1=f1, f2=f2, dih=dih, asp=asp, d=d, xbow=xmin)
print("saved; %.0fs" % (time.time() - t0))
