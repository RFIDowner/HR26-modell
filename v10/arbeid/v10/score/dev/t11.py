import sys; sys.path.insert(0, "..")
import numpy as np, score as S
tag = "fine"
V = np.load(f"V_{tag}.npy"); F = np.load(f"F_{tag}.npy"); lab = np.load(f"lab_{tag}.npy")
fn, area, cen, asp, lmax = S.face_geom(V, F)
cv = np.bincount(lab, weights=S.signed_volume(V, F))
ext = lab == int(np.argmax(cv))
topo = S.edge_topology(F, len(V))
skin = S.hull_skin_mask(cen, fn, ext)
f1, f2 = topo["f1"], topo["f2"]
both = skin[f1] & skin[f2]
ang = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", fn[f1], fn[f2]), -1, 1)))
big = both & (ang > 30)
mid = 0.5 * (V[topo["ev"][big, 0]] + V[topo["ev"][big, 1]])
for lo, hi in ((5400, 5800), (6400, 6800), (6900, 7400), (3200, 3400)):
    m = (mid[:, 0] > lo) & (mid[:, 0] < hi)
    print(lo, hi, m.sum(), "x", np.percentile(mid[m,0],[0,50,100]).round(0), "y", np.percentile(mid[m,1],[0,50,100]).round(0), "z", np.percentile(mid[m,2],[0,50,100]).round(0))
