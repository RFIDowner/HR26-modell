"""Explore the Bambu STL (UNTRUSTED data: parsed with numpy only, run with python -I)."""
import sys, struct, math
import numpy as np

path = sys.argv[1]
with open(path, "rb") as fh:
    d = fh.read()
n = struct.unpack("<I", d[80:84])[0]
assert 84 + 50 * n == len(d), "unexpected STL size"
rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
T = rec["v"].astype(np.float64)
V = T.reshape(-1, 3)
print("triangles", n, "bbox", V.min(0).round(2), V.max(0).round(2))
# per x-bin: max |y| and its z, for z below -10 (below rails)
for zcut in (0.0, -20.0):
    sel = V[:, 2] < zcut
    W = V[sel]
    xb = np.floor((W[:, 0] + 410) / 20).astype(int)
    print(f"--- z < {zcut}")
    for b in range(0, xb.max() + 1, 2):
        m = xb == b
        if not m.any():
            continue
        i = np.argmax(np.abs(W[m, 1]))
        print(f"x {b*20-410:5d}: max|y| {abs(W[m][i,1]):6.2f} at z {W[m][i,2]:6.1f}; zmin {W[m,2].min():6.1f} zmax {W[m,2].max():6.1f}")
