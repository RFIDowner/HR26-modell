import struct, sys
import numpy as np
exec(open("p9_badedges.py").read().split("for path in")[0])
P, F = load(sys.argv[1])
T = P[F]; ar = 0.5 * np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
deg = ar < 1e-10
c = T[deg].mean(1) * 30.0; c[:, 2] -= 1400.0
print("degenerate:", deg.sum())
for q in (0, 5, 25, 50, 75, 95, 100):
    print(f"  pct {q}: x {np.percentile(c[:,0], q):.0f} y {np.percentile(c[:,1], q):.1f} z {np.percentile(c[:,2], q):.1f}")
# klynger
xs = np.round(c[:, 0] / 10) * 10
u, n = np.unique(xs, return_counts=True)
print("x-klynger (10 mm):", list(zip(u[n > 50].tolist(), n[n > 50].tolist()))[:30])
# connected components: er de paa ytterskallet?
from collections import Counter
nv = len(P)
parent = np.arange(nv)
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
import sys as _s
_s.setrecursionlimit(10000)
# union-find vektorisert grovt
E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]]])
for a, b in E:
    ra, rb = find(a), find(b)
    if ra != rb: parent[ra] = rb
roots = np.array([find(v) for v in range(nv)])
lab = roots[F[:, 0]]
ul, cnt = np.unique(lab, return_counts=True)
big = ul[np.argmax(cnt)]
print("komponenter:", len(ul), "stoerste:", cnt.max(), "degenerate i stoerste:", int((deg & (lab == big)).sum()))
