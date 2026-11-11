import struct, sys
import numpy as np
from collections import Counter
def nm(path, tol=1e-4):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
    V = rec["v"].reshape(-1, 3).astype(np.float64)
    q = np.round(V / tol).astype(np.int64)
    uq, idx = np.unique(q, axis=0, return_inverse=True)
    idx = idx.reshape(-1, 3)
    e = np.sort(np.concatenate([idx[:, [0, 1]], idx[:, [1, 2]], idx[:, [2, 0]]]), axis=1)
    key = e[:, 0] * (len(uq) + 1) + e[:, 1]
    k, c = np.unique(key, return_counts=True)
    badk = k[c != 2]
    a = badk // (len(uq) + 1); b = badk % (len(uq) + 1)
    P = 0.5 * (uq[a] + uq[b]) * tol
    full = np.c_[P[:, 0] * 30 + 4, P[:, 1] * 30, P[:, 2] * 30 - 1400]
    return full, c[c != 2]
for p in sys.argv[1:]:
    F, cnt = nm(p)
    print(p, len(F), "counts", Counter(cnt.tolist()))
    # cluster by rounding to 100 mm
    keys = Counter([(int(x // 200) * 200, int(abs(y) // 200) * 200, int(z // 100) * 100) for x, y, z in F])
    for kk, v in sorted(keys.items(), key=lambda t: -t[1])[:25]:
        print("   x~%5d |y|~%5d z~%5d : %d" % (kk[0], kk[1], kk[2], v))
