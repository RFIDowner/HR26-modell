import sys, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-edges")
from vlib import *
from scipy.spatial import cKDTree
T0 = load_stl(OURS)
print("triangles", len(T0))
V0 = T0.reshape(-1,3)
Vu = np.unique(np.round(V0, 5), axis=0)
print("unique verts", len(Vu))
rng = np.random.default_rng(0)
sub = Vu[rng.choice(len(Vu), 20000, replace=False)]
for deg in np.arange(43.0, 46.51, 0.25):
    V = rot_z(Vu, -deg)
    yc = 0.5*(V[:,1].min()+V[:,1].max())
    V[:,1] -= yc
    tree = cKDTree(V)
    S = rot_z(sub, -deg); S[:,1] -= yc; S[:,1] *= -1
    d, _ = tree.query(S)
    print(f"{deg:6.2f}  mean mirror-NN {np.mean(d):.4f} mm  median {np.median(d):.4f}  bbox x {np.ptp(V[:,0]):.2f} y {np.ptp(V[:,1]):.2f}")
# mast hole: closed small loops in plan section at z where roof is (full ~1300)
for deg in (-44.0, -45.0):
    F = ours_full(deg, T0)
    for zf in (1300.0, 1330.0):
        lines = section_lines(F, 2, zf, keep=(0,1))
        small = []
        for L in lines:
            ext = np.ptp(L, axis=0)
            if ext.max() < 700 and np.linalg.norm(L[0]-L[-1]) < 1e-3:
                c = 0.5*(L.min(0)+L.max(0))
                small.append((c[0], c[1], ext[0], ext[1]))
        small.sort()
        print(f"rot {deg} z={zf}: closed loops <700:", [tuple(round(v,1) for v in s) for s in small])
