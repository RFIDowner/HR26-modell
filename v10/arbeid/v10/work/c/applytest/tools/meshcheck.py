"""Sjekker at en binaer STL er lukket og manifold."""
import struct
import sys
from collections import defaultdict

import numpy as np


def check(path, tol=1e-4):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    rec = np.frombuffer(
        d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]),
        count=n, offset=84,
    )
    V = rec["v"].reshape(-1, 3).astype(np.float64)
    q = np.round(V / tol).astype(np.int64)
    _, idx = np.unique(q, axis=0, return_inverse=True)
    idx = idx.reshape(-1, 3)
    edges = defaultdict(int)
    for tri in idx:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            u, v = tri[a], tri[b]
            edges[(min(u, v), max(u, v))] += 1
    bad = {k: c for k, c in edges.items() if c != 2}
    T = rec["v"].astype(np.float64)
    vol = abs(np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6.0)
    bb = V.min(0), V.max(0)
    print(f"{path}: {n} trekanter, {len(edges)} kanter, {len(bad)} ikke-manifolde")
    print(f"  volum {vol/1000:.1f} cm3   bbox {np.round(bb[1]-bb[0],1)}")
    return len(bad) == 0


if __name__ == "__main__":
    ok = all(check(p) for p in sys.argv[1:])
    sys.exit(0 if ok else 1)
