"""Step 3a: what reaches 01_skrog.stl - crease lines (deck edge, strake) in
full-scale coordinates. numpy only for the mesh."""
import sys, os, math, struct
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "repo"))
from hr26 import curves as C
from hr26 import params as P

STL = sys.argv[1]

def load(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
    return rec["v"].astype(np.float64)

T = load(STL)
a = math.radians(-45.0); c, s = math.cos(a), math.sin(a)
R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
T = T @ R.T
V = T.reshape(-1, 3)
V[:, 1] -= 0.5 * (V[:, 1].max() + V[:, 1].min())
xmin = V[:, 0].min()
print("model bbox", V.min(0), V.max(0))
# full scale: x from bow; first loft station is at x = 4.0
F = np.empty_like(V)
F[:, 0] = (V[:, 0] - xmin) * 30.0 + 4.0
F[:, 1] = V[:, 1] * 30.0
F[:, 2] = V[:, 2] * 30.0 - 1400.0
T = F.reshape(-1, 3, 3)
print("full bbox", F.min(0).round(1), F.max(0).round(1))

# weld vertices, triangle normals, edge adjacency
q, inv = np.unique(np.round(F, 3), axis=0, return_inverse=True)
inv = inv.reshape(-1, 3)
nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
area = np.linalg.norm(nrm, axis=1)
nrm /= (area[:, None] + 1e-12)
E = np.concatenate([inv[:, [0, 1]], inv[:, [1, 2]], inv[:, [2, 0]]])
tri = np.concatenate([np.arange(len(inv))] * 3)
Es = np.sort(E, axis=1)
key = Es[:, 0].astype(np.int64) * (len(q) + 1) + Es[:, 1]
order = np.argsort(key)
ks = key[order]
same = np.nonzero(ks[1:] == ks[:-1])[0]
e_i = order[same]; e_j = order[same + 1]
t1, t2 = tri[e_i], tri[e_j]
cosang = np.einsum("ij,ij->i", nrm[t1], nrm[t2])
dihed = np.degrees(np.arccos(np.clip(cosang, -1, 1)))
EV = Es[e_i]                      # vertex index pairs of interior edges
crease = dihed > 25.0
print(f"triangles {len(inv)}, verts {len(q)}, interior edges {len(EV)}, creases(>25deg) {crease.sum()}")
np.savez(os.path.join(HERE, "ours_mesh.npz"), q=q, inv=inv, nrm=nrm, EV=EV, dihed=dihed)

# alignment check: slice at x = const, outermost |y| near the sheer
def slice_x(T, x0):
    X = T[:, :, 0]
    sel = (X.min(1) < x0) & (X.max(1) > x0)
    Pp = T[sel]
    pts = []
    for a_, b_ in ((0, 1), (1, 2), (2, 0)):
        A, B = Pp[:, a_], Pp[:, b_]
        cr = (A[:, 0] - x0) * (B[:, 0] - x0) < 0
        t = (x0 - A[cr, 0]) / (B[cr, 0] - A[cr, 0])
        pts.append(A[cr] + t[:, None] * (B[cr] - A[cr]))
    return np.concatenate(pts)
for xx in (300, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 7500, 7800):
    S = slice_x(T, xx)
    zs = C.sheer_z(xx)
    s2 = S[np.abs(S[:, 2] - zs) < 60]
    i = np.argmax(np.abs(s2[:, 1]))
    print(f"x={xx}: max|y| near sheer = {abs(s2[i,1]):.1f}  hb={C.deck_half_breadth(xx):.1f}  (z {s2[i,2]:.1f}, sheer {zs:.1f}); max|y| all = {np.abs(S[:,1]).max():.1f}")

# ------------------------------------------------ deck-edge crease vertices
cv = np.unique(EV[crease].ravel())
P3 = q[cv]
hb = np.array([C.deck_half_breadth(v) for v in P3[:, 0]])
zs = np.array([C.sheer_z(v) for v in P3[:, 0]])
m = (P3[:, 1] > 0) & (np.abs(P3[:, 1] - hb) < 20) & (np.abs(P3[:, 2] - zs) < 20) & (P3[:, 0] > 30) & (P3[:, 0] < 7880)
de = P3[m]
de = de[np.argsort(de[:, 0])]
print("deck-edge crease vertices (stb):", len(de), " x-spacing median", np.median(np.diff(de[:, 0])).round(1), "max", np.diff(de[:, 0]).max().round(1))
np.save(os.path.join(HERE, "ours_deckedge.npy"), de)
print("  dy from deck_half_breadth: max", np.abs(de[:, 1] - np.array([C.deck_half_breadth(v) for v in de[:, 0]])).max().round(2),
      " dz from sheer_z: max", np.abs(de[:, 2] - np.array([C.sheer_z(v) for v in de[:, 0]])).max().round(2))

# ------------------------------------------------ strake crease vertices
# strake outer face corners: z = strake_z +- ~47 at ~55 outboard of the side
def side_y(x, z):
    sec = np.array(C.section(x, 60))
    return float(np.interp(z, sec[:, 1], sec[:, 0]))
zk = np.array([C.strake_z(v) for v in P3[:, 0]])
cand = (P3[:, 1] > 0) & (np.abs(P3[:, 2] - zk) < 75) & (P3[:, 0] > 150) & (P3[:, 0] < 7900)
idx = np.nonzero(cand)[0]
out = []
for i in idx:
    x, y, z = P3[i]
    sy = side_y(x, z)
    out.append(y - sy)
out = np.array(out)
st = P3[idx]
print("strake candidates", len(st), " offset from side: percentiles", np.percentile(out, [5, 25, 50, 75, 95]).round(1))
np.savez(os.path.join(HERE, "ours_strake.npz"), pts=st, off=out)
