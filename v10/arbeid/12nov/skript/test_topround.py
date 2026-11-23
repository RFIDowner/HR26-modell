import sys, os
sys.path.insert(0, sys.argv[1])
import cadquery as cq, numpy as np
from hr26 import hull as H, params as P, build as B, appendages as A
out = sys.argv[2]
def nm_edges(path):
    import struct
    d = open(path, "rb").read(); n = struct.unpack("<I", d[80:84])[0]
    rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
    T = rec["v"].astype(np.float64).reshape(-1, 3)
    q = np.round(T / 1e-5).astype(np.int64)
    u, inv = np.unique(q, axis=0, return_inverse=True)
    F = inv.reshape(-1, 3)
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    a = np.minimum(e[:, 0], e[:, 1]); b = np.maximum(e[:, 0], e[:, 1])
    key = a * np.int64(len(u)) + b
    _, cnt = np.unique(key, return_counts=True)
    return int((cnt != 2).sum())
base = cq.Workplane().newObject([H.hull_solid(40, 26)])
base = base.union(H.rubbing_strake())
for ex, n in ((8.0, 21), (20.0, 21), (20.0, 13), (30.0, 21)):
    P.TRANSOM_TOP_EXIT = ex
    c = H.transom_top_cutter(n=n)
    w = base.cut(c)
    m = B.to_model(w)
    fn = os.path.join(out, f"tt_{ex:g}_{n}.stl")
    m.val().exportStl(fn, 0.02, 0.15, False, False)
    print(f"exit {ex} n {n}: valid {w.val().isValid()} solider {B._n_solids(w)} ikke-manifold kanter {nm_edges(fn)}", flush=True)
