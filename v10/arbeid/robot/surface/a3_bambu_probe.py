import sys
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface")
from common import *
T32 = load_raw(sys.argv[1])
print("triangles", len(T32))
V, F = weld(T32)
print("verts", len(V))
fn, area = face_normals(V, F)
print("bbox", V.min(0).round(1), V.max(0).round(1))
c = V[F].mean(1)
# upward-facing area by z, and max |y| by z band in mid-hull
for z0 in range(-80, 60, 5):
    m = (c[:, 2] >= z0) & (c[:, 2] < z0 + 5)
    up = area[m & (fn[:, 2] > 0.8)].sum(); side = area[m & (np.abs(fn[:, 1]) > 0.7)].sum()
    mid = m & (np.abs(c[:, 0]) < 100)
    print(f"z {z0:4d}..{z0+5:4d}: faces {m.sum():6d} up-area {up:8.0f} side-area {side:8.0f}  max|y| mid {np.abs(c[mid,1]).max() if mid.sum() else 0:6.1f}")
lab = components(len(V), F)
ul, cnt = np.unique(lab, return_counts=True)
print("components", len(ul), "largest", np.sort(cnt)[::-1][:8])
E, f1, f2, counts = edges_adjacency(F)
print("edge multiplicity counts: 1:", (counts == 1).sum(), " 2:", (counts == 2).sum(), " >2:", (counts > 2).sum())
