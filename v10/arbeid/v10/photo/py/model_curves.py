"""Curves from the baseline mesh: strake outer y(x), deck edge (max y at sheer) etc. Saved to model_curves.npz"""
import sys, csv, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/py")
from stl import load_full
REPO = r"C:/Users/stig/Documents/GitHub/HR26-modell"
V, F = load_full()
rows = list(csv.DictReader(open(f"{REPO}/data/hull_stations.csv")))
xs = np.array([float(r["x_from_bow_mm"]) for r in rows]); zs = np.array([float(r["strake_z_mm"]) for r in rows])
hb = np.array([float(r["deck_half_breadth_mm"]) for r in rows])
DEZ = np.array([(0.0, 1204.0), (1000.0, 1204.0), (2000.0, 1200.0), (2500.0, 1175.0), (3000.0, 1150.0), (3750.0, 1122.0), (4200.0, 1115.0), (4500.0, 1105.0), (5000.0, 1095.0), (5500.0, 1085.0), (6000.0, 1080.0), (6500.0, 1075.0), (7000.0, 1056.0), (7200.0, 1040.0), (7400.0, 1020.0), (7600.0, 992.0), (7800.0, 962.0), (7950.0, 940.0)])
X = np.arange(100, 7951, 50.0)
ys, zst, ytop, ybot = [], [], [], []
P = V[V[:, 1] > 0]
for x in X:
    z0 = np.interp(x, xs, zs)
    m = (np.abs(P[:, 0] - x) < 25) & (np.abs(P[:, 2] - z0) < 80)
    if m.sum() == 0:
        ys.append(np.nan); zst.append(np.nan); continue
    q = P[m]; i = np.argmax(q[:, 1]); ys.append(q[i, 1]); zst.append(q[i, 2])
ys = np.array(ys)
# sheer: max y among vertices with z within 30 of deck edge z
yd = []
for x in X:
    z0 = np.interp(x, DEZ[:, 0], DEZ[:, 1])
    m = (np.abs(P[:, 0] - x) < 25) & (np.abs(P[:, 2] - z0) < 25)
    yd.append(P[m, 1].max() if m.sum() else np.nan)
np.savez(r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/model_curves.npz", X=X, strake_y=ys, strake_z=np.interp(X, xs, zs), deck_y=np.array(yd), deck_z=np.interp(X, DEZ[:, 0], DEZ[:, 1]), hb=np.interp(X, xs, hb))
for x in (100, 500, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 7500, 7800, 7900):
    i = np.argmin(abs(X - x)); print(x, "strake y %.0f  deck y %.0f  hb(csv) %.0f" % (ys[i], yd[i], np.interp(x, xs, hb)))
