"""Bambu hull outline by exact plane slices (UNTRUSTED STL: numpy only, run with python -I).
Outputs per x (full scale, aligned to ours): max |y| in the hull band and its z,
plus the hull-side top (sheer) z = highest z where |y| >= max|y| - 25 mm."""
import sys, os, struct
import numpy as np

path, out = sys.argv[1], sys.argv[2]
with open(path, "rb") as fh:
    d = fh.read()
n = struct.unpack("<I", d[80:84])[0]
assert 84 + 50 * n == len(d)
rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
T = rec["v"].astype(np.float64)
k = 0.3708
V = T.reshape(-1, 3)
band = V[(V[:, 2] < -20.0) & (V[:, 2] > -60.0)]
xbow = band[:, 0].min()
F = np.empty_like(V)
F[:, 0] = (V[:, 0] - xbow) * k * 30.0 + 4.0
F[:, 1] = V[:, 1] * k * 30.0 * 1.223
F[:, 2] = ((V[:, 2] + 37.4) * k + 83.1) * 30.0 - 1400.0
T = F.reshape(-1, 3, 3)
zlo = ((-75.0 + 37.4) * k + 83.1) * 30.0 - 1400.0
zhi = ((-15.0 + 37.4) * k + 83.1) * 30.0 - 1400.0
keep = (T[:, :, 2].max(1) > zlo) & (T[:, :, 2].min(1) < zhi)
T = T[keep]
X = T[:, :, 0]; xmn, xmx = X.min(1), X.max(1)
xs = np.arange(20.0, 7900.0, 10.0)
ymax = np.full(len(xs), np.nan); zat = np.full(len(xs), np.nan); ztop = np.full(len(xs), np.nan)
for i, x0 in enumerate(xs):
    sel = (xmn < x0) & (xmx > x0)
    P = T[sel]
    pts = []
    for a_, b_ in ((0, 1), (1, 2), (2, 0)):
        A, B = P[:, a_], P[:, b_]
        cr = (A[:, 0] - x0) * (B[:, 0] - x0) < 0
        t = (x0 - A[cr, 0]) / (B[cr, 0] - A[cr, 0])
        pts.append(A[cr] + t[:, None] * (B[cr] - A[cr]))
    S = np.concatenate(pts)
    S = S[(S[:, 2] > zlo) & (S[:, 2] < zhi)]
    if len(S) < 4:
        continue
    j = np.argmax(np.abs(S[:, 1]))
    ymax[i] = abs(S[j, 1]); zat[i] = S[j, 2]
np.savez(out, x=xs, y=ymax, z=zat)
ok = ~np.isnan(ymax)
print("Bambu slices:", ok.sum(), "of", len(xs), " x range with data", xs[ok].min(), xs[ok].max())
