"""Hvor ligger de ikke-manifolde kantene? (python -I, numpy)"""
import struct, sys
import numpy as np
def load(path, tol=1e-4):
    d = open(path, "rb").read(); n = struct.unpack("<I", d[80:84])[0]
    rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
    V = rec["v"].reshape(-1, 3).astype(np.float64)
    q = np.round(V / tol).astype(np.int64)
    u, inv = np.unique(q, axis=0, return_inverse=True)
    F = inv.reshape(-1, 3)
    P = u * tol
    return P, F
for path in sys.argv[1:]:
    P, F = load(path)
    e = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    key = e[:, 0] * (len(P) + 1) + e[:, 1]
    uk, cnt = np.unique(key, return_counts=True)
    bad = uk[cnt != 2]
    a = bad // (len(P) + 1); b = bad % (len(P) + 1)
    mid = 0.5 * (P[a] + P[b]) * 30.0      # fullskala-ish (fra baugen, keel z=0)
    mid[:, 2] -= 1400.0
    print(path, "bad", len(bad), "count hist", dict(zip(*np.unique(cnt[cnt != 2], return_counts=True))))
    # degenererte trekanter
    T = P[F]; ar = 0.5 * np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
    print("  degenererte trekanter (areal < 1e-10):", int((ar < 1e-10).sum()), " samme indeks to ganger:", int(((F[:, 0] == F[:, 1]) | (F[:, 1] == F[:, 2]) | (F[:, 0] == F[:, 2])).sum()))
    if len(bad):
        H, xe = np.histogram(mid[:, 0], bins=np.arange(-100, 8100, 400))
        print("  x-histogram:", {int(x): int(h) for x, h in zip(xe[:-1], H) if h})
        H, ze = np.histogram(mid[:, 2], bins=np.arange(-1500, 1800, 200))
        print("  z-histogram:", {int(z): int(h) for z, h in zip(ze[:-1], H) if h})
        H, ye = np.histogram(np.abs(mid[:, 1]), bins=np.arange(0, 1500, 100))
        print("  |y|-histogram:", {int(y): int(h) for y, h in zip(ye[:-1], H) if h})
