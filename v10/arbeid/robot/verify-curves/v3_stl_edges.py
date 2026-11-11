"""Independent extraction of the deck-edge crease, strake corner and topside facet sizes
from 01_skrog.stl (rotated -45 deg, converted to full-scale mm from the bow / DWL)."""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-curves/repo")
import numpy as np
from hr26 import curves as C, params as P

D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-curves/"
tri = np.load(D + "tri.npy")


def to_full(tri, ang=45.0):
    a = np.radians(-ang)
    c, s = np.cos(a), np.sin(a)
    V = tri.reshape(-1, 3)
    R = np.c_[c * V[:, 0] - s * V[:, 1], s * V[:, 0] + c * V[:, 1], V[:, 2]]
    return R


R = to_full(tri)
xmin, xmax = R[:, 0].min(), R[:, 0].max()
F = np.c_[(R[:, 0] - xmin) * 30.0 + 4.0, R[:, 1] * 30.0, R[:, 2] * 30.0 - 1400.0]
print("full-scale x range %.1f .. %.1f  (expect 4 .. ~7950)" % (F[:, 0].min(), F[:, 0].max()))
print("y range %.1f .. %.1f ; z range %.1f .. %.1f" % (F[:, 1].min(), F[:, 1].max(), F[:, 2].min(), F[:, 2].max()))

# --- unique vertices / connectivity
key = np.round(R / 1e-5).astype(np.int64)
uk, inv = np.unique(key, axis=0, return_inverse=True)
inv = inv.ravel()
Vf = np.zeros((len(uk), 3))
Vf[inv] = F
T = inv.reshape(-1, 3)
print("unique vertices", len(uk), "triangles", len(T))
P0, P1, P2 = Vf[T[:, 0]], Vf[T[:, 1]], Vf[T[:, 2]]
N = np.cross(P1 - P0, P2 - P0)
A2 = np.linalg.norm(N, axis=1)
N = N / np.where(A2 > 0, A2, 1)[:, None]
E = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
tid = np.tile(np.arange(len(T)), 3)
Es = np.sort(E, axis=1)
order = np.lexsort((Es[:, 1], Es[:, 0]))
Es, tid = Es[order], tid[order]
same = np.all(Es[1:] == Es[:-1], axis=1)
i = np.where(same)[0]
pairs = Es[i]
ta, tb = tid[i], tid[i + 1]
cosang = np.einsum("ij,ij->i", N[ta], N[tb])
print("manifold edge pairs", len(pairs))

# --- deck-edge crease on y>0: one face deck-like (nz>0.95), the other side-like (|nz|<0.7, ny>0.5)
def side_like(n):
    return (np.abs(n[:, 2]) < 0.7) & (n[:, 1] > 0.5)

deckA, deckB = N[ta, 2] > 0.95, N[tb, 2] > 0.95
cand = (deckA & side_like(N[tb])) | (deckB & side_like(N[ta]))
mid = 0.5 * (Vf[pairs[:, 0]] + Vf[pairs[:, 1]])
zs = np.array([C.sheer_z(x) for x in mid[:, 0]])
hbm = np.array([C.deck_half_breadth(x) for x in mid[:, 0]])
cand &= (np.abs(mid[:, 2] - zs) < 30) & (mid[:, 1] > 0) & (np.abs(mid[:, 1] - hbm) < 30)
ce = pairs[cand]
vids = np.unique(ce.ravel())
pts = Vf[vids]
pts = pts[np.argsort(pts[:, 0])]
print("\nDeck-edge crease (stb): %d edges, %d vertices" % (cand.sum(), len(pts)))
for p in pts:
    print("   x=%7.1f y=%7.1f z=%7.1f   hb(x)=%7.1f  sheer(x)=%7.1f   dy=%+6.1f dz=%+6.1f" % (
        p[0], p[1], p[2], C.deck_half_breadth(p[0]), C.sheer_z(p[0]),
        p[1] - C.deck_half_breadth(p[0]), p[2] - C.sheer_z(p[0])))
np.save(D + "stl_deckedge.npy", pts)

# check: are there gaps? segments and corner angles in plan and profile
seg = np.diff(pts[:, :2], axis=0)
L = np.linalg.norm(np.diff(pts, axis=0), axis=1)
hd = np.degrees(np.arctan2(seg[:, 1], seg[:, 0]))
pr = np.degrees(np.arctan2(np.diff(pts[:, 2]), np.diff(pts[:, 0])))
print("segment lengths (full mm):", np.round(L, 0))
print("plan corner angles (deg):", np.round(np.diff(hd), 2))
print("profile corner angles (deg):", np.round(np.diff(pr), 2))
np.savez(D + "stl_mesh_full.npz", V=Vf, T=T, N=N)
