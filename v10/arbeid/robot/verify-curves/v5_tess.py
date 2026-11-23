"""Compare tessellations: final 01_skrog.stl vs re-tessellated bare loft (relative / absolute).
Deck-edge polyline vertices + chord error vs the exact B-rep edge; waterline cut error vs exact
B-rep waterline; topside facet dihedral angles and triangle density."""
import sys
sys.dont_write_bytecode = True
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-curves/"
sys.path.insert(0, D + "repo")
import numpy as np
from hr26 import curves as C

BRE = np.load(D + "brep_deckedge.npy")
WL = np.load(D + "brep_waterlines.npz")


def load(fn):
    with open(fn, "rb") as f:
        f.read(80)
        n = int(np.frombuffer(f.read(4), np.uint32)[0])
        dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        rec = np.frombuffer(f.read(n * 50), dt, count=n)
    tri = rec["v"].astype(np.float64)
    V = tri.reshape(-1, 3)
    a = np.radians(-45.0)
    c, s = np.cos(a), np.sin(a)
    R = np.c_[c * V[:, 0] - s * V[:, 1], s * V[:, 0] + c * V[:, 1], V[:, 2]]
    F = np.c_[(R[:, 0] - R[:, 0].min()) * 30.0 + 4.0, R[:, 1] * 30.0, R[:, 2] * 30.0]
    return F.reshape(-1, 3, 3)


def mesh(tri):
    V = tri.reshape(-1, 3)
    key = np.round(V * 1e3).astype(np.int64)   # 0.001 full-mm grid
    uk, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.ravel()
    Vu = np.zeros((len(uk), 3)); Vu[inv] = V
    T = inv.reshape(-1, 3)
    P0, P1, P2 = Vu[T[:, 0]], Vu[T[:, 1]], Vu[T[:, 2]]
    N = np.cross(P1 - P0, P2 - P0); A = 0.5 * np.linalg.norm(N, axis=1)
    N /= np.where(A > 0, 2 * A, 1)[:, None]
    E = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    tid = np.tile(np.arange(len(T)), 3)
    Es = np.sort(E, axis=1)
    o = np.lexsort((Es[:, 1], Es[:, 0])); Es, tid = Es[o], tid[o]
    i = np.where(np.all(Es[1:] == Es[:-1], axis=1))[0]
    return Vu, T, N, A, Es[i], tid[i], tid[i + 1]


def zoff(tri, z_keel_known):
    return tri


def analyse(fn, label, z_from_keel=True):
    tri = load(fn)
    if z_from_keel:
        tri[..., 2] -= 1400.0          # 01_skrog: z=0 at keel bottom (-1400)
    else:
        # bare loft: lowest point is the canoe bottom; shift so that the deck edge matches
        tri[..., 2] += -505.7127628695013 - tri[..., 2].min()
    Vu, T, N, A, pairs, ta, tb = mesh(tri)
    print(f"\n=== {label}: {len(T)} triangles")
    # deck edge vertices (stb)
    mid = 0.5 * (Vu[pairs[:, 0]] + Vu[pairs[:, 1]])
    side = lambda n: (np.abs(n[:, 2]) < 0.7) & (n[:, 1] > 0.5)
    cand = ((N[ta, 2] > 0.95) & side(N[tb])) | ((N[tb, 2] > 0.95) & side(N[ta]))
    hb = np.interp(mid[:, 0], BRE[:, 0], BRE[:, 1]); zs = np.interp(mid[:, 0], BRE[:, 0], BRE[:, 2])
    cand &= (mid[:, 1] > 0) & (np.abs(mid[:, 1] - hb) < 30) & (np.abs(mid[:, 2] - zs) < 30)
    v = np.unique(pairs[cand].ravel())
    p = Vu[v]; p = p[np.argsort(p[:, 0])]
    p = p[(p[:, 0] > 300) & (p[:, 0] < 7705)]
    print(f"  deck-edge vertices in x 300-7705: {len(p)}; segment dx max {np.diff(p[:,0]).max():.0f}, median {np.median(np.diff(p[:,0])):.0f}")
    hd = np.degrees(np.arctan2(np.diff(p[:, 1]), np.diff(p[:, 0])))
    pr = np.degrees(np.arctan2(np.diff(p[:, 2]), np.diff(p[:, 0])))
    print(f"  plan corners: max {np.abs(np.diff(hd)).max():.2f} deg, median {np.median(np.abs(np.diff(hd))):.2f}; profile corners max {np.abs(np.diff(pr)).max():.2f}")
    # chord error against exact B-rep edge
    errs_y, errs_z = [], []
    for a, b in zip(p[:-1], p[1:]):
        xs = np.linspace(a[0], b[0], 60)
        yc = np.interp(xs, [a[0], b[0]], [a[1], b[1]]); zc = np.interp(xs, [a[0], b[0]], [a[2], b[2]])
        errs_y.append(np.abs(yc - np.interp(xs, BRE[:, 0], BRE[:, 1])).max())
        errs_z.append(np.abs(zc - np.interp(xs, BRE[:, 0], BRE[:, 2])).max())
    print(f"  chord error vs B-rep: plan max {max(errs_y):.2f} mm (model {max(errs_y)/30:.3f}), profile max {max(errs_z):.2f} mm")
    # waterline cuts vs B-rep waterlines (x 1500-6800, y>0)
    for z0 in [150.0, 400.0, 700.0]:
        z = tri[..., 2] - z0
        s = np.sign(z)
        cross = (s.min(1) < 0) & (s.max(1) > 0)
        pts = []
        for t, zz in zip(tri[cross], z[cross]):
            q = []
            for i, j in ((0, 1), (1, 2), (2, 0)):
                if zz[i] * zz[j] < 0:
                    f = zz[i] / (zz[i] - zz[j]); q.append(t[i] + f * (t[j] - t[i]))
            if len(q) == 2:
                pts.append(q[0]); pts.append(q[1])
        pts = np.array(pts)
        ref = WL[f"z{int(z0)}"]
        m = (pts[:, 1] > 0) & (pts[:, 0] > 1500) & (pts[:, 0] < 6800)
        # outer hull only (not the inside of a hollowed shell): keep points near the B-rep line
        yref = np.interp(pts[m, 0], ref[:, 0], ref[:, 1])
        d = pts[m, 1] - yref
        keep = np.abs(d) < 15
        # error at segment midpoints: use the crossing segments
        segs = pts.reshape(-1, 2, 3)
        mm = (segs[:, :, 1].min(1) > 0) & (segs[:, :, 0].min(1) > 1500) & (segs[:, :, 0].max(1) < 6800)
        sg = segs[mm]
        midp = sg.mean(1)
        yref2 = np.interp(midp[:, 0], ref[:, 0], ref[:, 1])
        dd = midp[:, 1] - yref2
        ok = np.abs(dd) < 15
        L = np.abs(sg[ok, 1, 0] - sg[ok, 0, 0])
        print(f"  waterline z=+{z0:.0f}: {ok.sum()} segments in x 1500-6800, segment dx median {np.median(L):.0f} max {L.max():.0f} mm; "
              f"mid-chord error max {np.abs(dd[ok]).max():.2f} mm (model {np.abs(dd[ok]).max()/30:.3f})")
    # topside facets: side-facing triangles above DWL, below deck edge
    cen = (Vu[T[:, 0]] + Vu[T[:, 1]] + Vu[T[:, 2]]) / 3
    zsc = np.interp(cen[:, 0], BRE[:, 0], BRE[:, 2])
    top = (cen[:, 0] > 1500) & (cen[:, 0] < 6800) & (cen[:, 2] > 0) & (cen[:, 2] < zsc - 15) & (N[:, 1] > 0.6) & (cen[:, 1] > 0)
    hbc = np.interp(cen[:, 0], BRE[:, 0], BRE[:, 1])
    top &= cen[:, 1] > 0.7 * hbc
    idx = np.where(top)[0]
    ext = np.ptp(Vu[T[idx]][:, :, 0], axis=1)
    sel = np.zeros(len(T), bool); sel[idx] = True
    both = sel[ta] & sel[tb]
    ang = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", N[ta[both]], N[tb[both]]), -1, 1)))
    area = A[idx].sum() / 1e6
    print(f"  topside (x1500-6800, DWL..deck, stb): {len(idx)} triangles over {area:.2f} m2 = {len(idx)/area:.0f}/m2 "
          f"(model: {len(idx)/(area*1e6/900):.2f}/mm2); triangle x-extent median {np.median(ext):.0f} mm, 90% {np.percentile(ext,90):.0f}")
    print(f"  dihedral between neighbouring topside facets: median {np.median(ang):.2f}, 90% {np.percentile(ang,90):.2f}, max {ang.max():.2f} deg")
    return p


p0 = analyse(r"C:/Users/stig/Documents/GitHub/HR26-modell/export/stl/01_skrog.stl", "01_skrog.stl (as exported)")
np.save(D + "stl_deck_vertices.npy", p0)
for tag in ["rel_0.018_0.12", "abs_0.018_0.12", "abs_0.01_0.05"]:
    analyse(D + f"loft_{tag}.stl", f"bare loft {tag}", z_from_keel=False)
