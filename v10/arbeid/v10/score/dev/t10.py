import sys; sys.path.insert(0, "..")
import numpy as np, score as S
for tag in ["skrog", "fine"]:
    V = np.load(f"V_{tag}.npy"); F = np.load(f"F_{tag}.npy"); lab = np.load(f"lab_{tag}.npy")
    fn, area, cen, asp, lmax = S.face_geom(V, F)
    vol = S.signed_volume(V, F)
    cv = np.bincount(lab, weights=vol)
    ext = lab == int(np.argmax(cv))
    topo = S.edge_topology(F, len(V))
    skin = S.hull_skin_mask(cen, fn, ext)
    f1, f2 = topo["f1"], topo["f2"]
    both = skin[f1] & skin[f2]
    ang = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", fn[f1], fn[f2]), -1, 1)))
    big = both & (ang > 30)
    mid = 0.5 * (V[topo["ev"][big, 0]] + V[topo["ev"][big, 1]])
    print(tag, "skin edges >30deg:", big.sum())
    # cluster by x
    h, e = np.histogram(mid[:, 0], bins=np.arange(0, 8100, 250))
    print("  x-hist:", [(int(a), int(b)) for a, b in zip(e[:-1], h) if b])
    print("  z range:", np.percentile(mid[:, 2], [0, 25, 50, 75, 100]).round(0) if len(mid) else None, " |y| range", np.percentile(np.abs(mid[:, 1]), [0, 50, 100]).round(0) if len(mid) else None)
    print("  sample:", mid[:12].round(0).tolist())
