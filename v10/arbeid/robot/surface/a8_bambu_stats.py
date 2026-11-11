import sys
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface")
from common import *
T32 = load_raw(sys.argv[1]); V, F = weld(T32); V = V * 0.3708       # same length as ours, model mm
fn, area = face_normals(V, F); c = V[F].mean(1)
zmb = -37.4 * 0.3708
# topsides below max beam, outward, away from bow/stern ends
side = (c[:, 2] < zmb - 0.5) & (c[:, 2] > -110 * 0.3708) & (c[:, 1] * fn[:, 1] > 0) & (np.abs(fn[:, 2]) < 0.8) & (np.abs(c[:, 1]) > 0.5 * 98.5 * 0.3708)
E, f1, f2, cnt = edges_adjacency(F)
both = side[f1] & side[f2]
dih = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", fn[f1], fn[f2]), -1, 1)))[both]
el = np.stack([np.linalg.norm(V[F[:, i]] - V[F[:, (i + 1) % 3]], axis=1) for i in range(3)], 1)
lmax = el.max(1); asp = lmax / np.maximum(2 * area / np.maximum(lmax, 1e-12), 1e-12)
print(f"Bambu topsides: {side.sum()} tri, area {area[side].sum():.0f} mm2 -> {side.sum()/area[side].sum():.1f} tri/mm2")
print("  edge length p5/p50/p95/max (model mm):", np.round(np.percentile(el[side].ravel(), [5, 50, 95, 100]), 3))
print("  aspect p50/p90:", np.round(np.percentile(asp[side], [50, 90]), 2), f" share aspect>10 {np.mean(asp[side]>10)*100:.1f}%  >20 {np.mean(asp[side]>20)*100:.2f}%")
print(f"  dihedral p50 {np.percentile(dih,50):.2f} p90 {np.percentile(dih,90):.2f} p99 {np.percentile(dih,99):.2f};  >2deg {np.mean(dih>2)*100:.1f}%  >5deg {np.mean(dih>5)*100:.2f}%  >10deg {np.mean(dih>10)*100:.2f}%")
