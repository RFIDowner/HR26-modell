"""Step 3b: the deck-edge and strake lines as they are in 01_skrog.stl and the
corresponding lines on the Bambu mesh. Run with python -I (reads untrusted STL).
argv: ours.stl bambu.stl"""
import sys, os, math, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "repo"))
import numpy as np
from hr26 import curves as C
from hr26 import params as P

def load(path):
    with open(path, "rb") as fh:
        d = fh.read()
    n = struct.unpack("<I", d[80:84])[0]
    assert 84 + 50 * n == len(d)
    rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
    return rec["v"].astype(np.float64)

def mesh_topology(T):
    F = T.reshape(-1, 3)
    q, inv = np.unique(np.round(F, 3), axis=0, return_inverse=True)
    inv = inv.reshape(-1, 3)
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    nrm /= (np.linalg.norm(nrm, axis=1)[:, None] + 1e-12)
    E = np.concatenate([inv[:, [0, 1]], inv[:, [1, 2]], inv[:, [2, 0]]])
    tri = np.concatenate([np.arange(len(inv))] * 3)
    Es = np.sort(E, axis=1)
    key = Es[:, 0].astype(np.int64) * (len(q) + 1) + Es[:, 1]
    o = np.argsort(key); ks = key[o]
    same = np.nonzero(ks[1:] == ks[:-1])[0]
    a, b = o[same], o[same + 1]
    dih = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", nrm[tri[a]], nrm[tri[b]]), -1, 1)))
    return q, Es[a], dih

def turning(P2):
    """turning angle (deg) at interior vertices of a 2D polyline."""
    d = np.diff(P2, axis=0)
    th = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    return np.diff(th)

# ------------------------------------------------------------- ours
T = load(sys.argv[1])
a = math.radians(-45.0); c, s = math.cos(a), math.sin(a)
T = T @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T
V = T.reshape(-1, 3)
V[:, 1] -= 0.5 * (V[:, 1].max() + V[:, 1].min())
x0 = V[:, 0].min()
V[:, 0] = (V[:, 0] - x0) * 30.0 + 4.0; V[:, 1] *= 30.0; V[:, 2] = V[:, 2] * 30.0 - 1400.0
T = V.reshape(-1, 3, 3)
q, EV, dih = mesh_topology(T)
cr = dih > 25.0
cv = np.unique(EV[cr].ravel()); Q = q[cv]
hb = np.array([C.deck_half_breadth(v) for v in Q[:, 0]]); zs = np.array([C.sheer_z(v) for v in Q[:, 0]])
m = (Q[:, 1] > 0) & (np.abs(Q[:, 1] - hb) < 20) & (np.abs(Q[:, 2] - zs) < 20)
de = Q[m]; de = de[np.argsort(de[:, 0])]
print(f"OURS deck-edge polyline: {len(de)} vertices; between x=400 and 7650: {((de[:,0]>400)&(de[:,0]<7650)).sum()}")
mid = de[(de[:, 0] > 300) & (de[:, 0] < 7710)]
seg = np.diff(mid[:, 0])
print("  vertex x:", np.round(mid[:, 0]).astype(int).tolist())
print("  segment lengths (mm):", np.round(seg).astype(int).tolist())
tp = turning(mid[:, [0, 1]]); tz = turning(mid[:, [0, 2]])
print("  plan turning at vertices (deg):", np.round(tp, 2).tolist())
print("  profile turning at vertices (deg):", np.round(tz, 2).tolist())
# chord deviation from the true curves along each segment
dev_y, dev_z = [], []
for p0, p1 in zip(mid[:-1], mid[1:]):
    xx = np.linspace(p0[0], p1[0], 60)
    yc = np.interp(xx, [p0[0], p1[0]], [p0[1], p1[1]]); zc = np.interp(xx, [p0[0], p1[0]], [p0[2], p1[2]])
    yt = np.array([C.deck_half_breadth(v) for v in xx]); zt = np.array([C.sheer_z(v) for v in xx])
    dev_y.append(np.abs(yt - yc).max()); dev_z.append(np.abs(zt - zc).max())
print("  max chord deviation plan (mm full):", np.round(dev_y, 1).tolist())
print("  max chord deviation profile (mm full):", np.round(dev_z, 1).tolist())

# strake outer corners: crease vertices 40..75 mm outboard of the side at that height
def side_y(x, z):
    sec = np.array(C.section(x, 60)); return float(np.interp(z, sec[:, 1], sec[:, 0]))
zk = np.array([C.strake_z(v) for v in Q[:, 0]])
cand = np.nonzero((Q[:, 1] > 0) & (np.abs(Q[:, 2] - zk) < 70) & (Q[:, 0] > 150))[0]
off = np.array([Q[i, 1] - side_y(Q[i, 0], Q[i, 2]) for i in cand])
S = Q[cand][off > 35.0]
top = S[S[:, 2] > np.array([C.strake_z(v) for v in S[:, 0]])]
bot = S[S[:, 2] <= np.array([C.strake_z(v) for v in S[:, 0]])]
top = top[np.argsort(top[:, 0])]; bot = bot[np.argsort(bot[:, 0])]
# keep the outermost vertex per 5 mm x cluster
def thin(A):
    out = [A[0]]
    for p in A[1:]:
        if p[0] - out[-1][0] > 5.0: out.append(p)
        elif p[1] > out[-1][1]: out[-1] = p
    return np.array(out)
top = thin(top); bot = thin(bot)
print(f"OURS strake top-outer corner: {len(top)} vertices, x {top[0,0]:.0f}-{top[-1,0]:.0f}")
st_x = np.array([x for x in C.stations(48) if P.STRAKE_X0 < x])
print("  strake loft stations (C.stations(48) > 200):", np.round(st_x).astype(int).tolist()[:60])
tsel = top[(top[:, 0] > 1000) & (top[:, 0] < 7400)]
print("  vertex x (1000-7400):", np.round(tsel[:, 0]).astype(int).tolist())
print("  plan turning (deg):", np.round(turning(tsel[:, [0, 1]]), 2).tolist())
print("  profile turning (deg):", np.round(turning(tsel[:, [0, 2]]), 2).tolist())

# ------------------------------------------------------------- Bambu
B = load(sys.argv[2]).reshape(-1, 3)
k = 0.3708
band = B[(B[:, 2] < -20.0) & (B[:, 2] > -60.0)]
xbow = band[:, 0].min()
Bf = np.empty_like(B)
Bf[:, 0] = (B[:, 0] - xbow) * k * 30.0 + 4.0
Bf[:, 1] = B[:, 1] * k * 30.0 * 1.223
Bf[:, 2] = ((B[:, 2] + 37.4) * k + 83.1) * 30.0 - 1400.0
print("BAMBU full-scale bbox", Bf.min(0).round(0), Bf.max(0).round(0))
# plan outline = max |y| per 10 mm x-bin, hull band only (below rails)
zlim = ((-20.0 + 37.4) * k + 83.1) * 30.0 - 1400.0
H = Bf[Bf[:, 2] < zlim]
xb = np.floor(H[:, 0] / 10.0).astype(int)
nb = xb.max() + 1
ymax = np.full(nb, np.nan); zat = np.full(nb, np.nan)
o = np.lexsort((np.abs(H[:, 1]), xb))
last = np.r_[np.nonzero(np.diff(xb[o]))[0], len(o) - 1]
ymax[xb[o][last]] = np.abs(H[o][last, 1]); zat[xb[o][last]] = H[o][last, 2]
bx = (np.arange(nb) + 0.5) * 10.0
ok = ~np.isnan(ymax)
np.savez(os.path.join(HERE, "lines.npz"), de=de, top=top, bot=bot,
         b_x=bx[ok], b_y=ymax[ok], b_z=zat[ok])
# our own plan outline computed the SAME way (max |y| per 10 mm bin, all z)
xo = np.floor(V[:, 0] / 10.0).astype(int)
ymo = np.zeros(xo.max() + 1); np.maximum.at(ymo, xo, np.abs(V[:, 1]))
np.save(os.path.join(HERE, "ours_maxy.npy"), ymo)
print("Bambu outline samples", ok.sum(), " max y", np.nanmax(ymax).round(1), " z of max-beam line: median", np.nanmedian(zat).round(0))
