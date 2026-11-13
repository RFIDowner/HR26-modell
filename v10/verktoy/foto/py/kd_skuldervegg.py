"""Veggtykkelsen under skulderen over knekken (V10 trinn 8), maalt paa STL-en.

Poengkortets veggmaal ser bare skrogsiden under knekken og det flate dekket;
den skraa skulderen ligger utenfor begge. Her trekkes punkter paa skulderens
flate (normal 30-55 grader fra loddrett, mellom knekken og karmtoppen), og en
straale sendes rett inn i godset til den treffer neste flate.

  python ../../../../tools/memcap.py --gb 3 -- python kd_skuldervegg.py [01_skrog.stl]
"""
import sys

import numpy as np

sys.path.insert(0, __file__.replace("\\", "/").rsplit("/", 4)[0] + "/arbeid/v10/score")
import score as S          # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else "../../../../export/stl/01_skrog.stl"
T = S.load_stl(path)
if isinstance(T, tuple):
    T = T[0]
Vm, F = S.weld(T)
fr = S.detect_frame(Vm, "auto")
V = S.to_build_frame(Vm, fr, 4.0)
fn, area, cen, aspect, lmax = S.face_geom(V, F)
x, y, z = cen[:, 0], cen[:, 1], cen[:, 2]
ang = np.degrees(np.arccos(np.clip(fn[:, 2], -1, 1)))            # fra loddrett
out = fn[:, 1] * np.sign(y) > 0.3
zk = np.array([float(S.knuckle_meas(v)) for v in x])
hb = np.array([float(S.hb_meas(v)) for v in x])
m = (x > 5250) & (x < 7700) & (ang > 30) & (ang < 55) & out & (z > zk - 5) & (z < zk + 230) & (np.abs(y) > hb - 260)
idx = np.nonzero(m)[0]
print("skulderflater:", len(idx), "trekanter, areal %.0f cm2 (fullskala)" % (area[idx].sum() / 100))
rng = np.random.default_rng(3)
n = 6000
fs = idx[rng.choice(len(idx), size=n, p=area[idx] / area[idx].sum())]
a, b = rng.random(n), rng.random(n)
fl = a + b > 1
a[fl], b[fl] = 1 - a[fl], 1 - b[fl]
P = V[F[fs, 0]] + a[:, None] * (V[F[fs, 1]] - V[F[fs, 0]]) + b[:, None] * (V[F[fs, 2]] - V[F[fs, 0]])
d = -fn[fs]
O = P + 0.05 * d
Tt = V[F]
fb = (Tt.min(1), Tt.max(1))
t = np.full(n, np.inf)
for part in np.array_split(np.argsort(O[:, 0]), 4):
    t[part], _ = S.ray_cast(V, F, O[part], d[part], 400.0, 30.0, bounds=fb)
tm = (t + 0.05) / S.SCALE
fin = np.isfinite(tm)
print("straaler %d; massivt eller over 13 mm: %.0f %%" % (n, 100 * np.mean(~fin)))
print("vegg under skulderen (modell-mm): min %.2f  p1 %.2f  p5 %.2f  median %.2f" % (
    tm[fin].min(), np.percentile(tm[fin], 1), np.percentile(tm[fin], 5), np.median(tm[fin])))
o = np.argsort(np.where(fin, tm, np.inf))[:6]
for i in o:
    print("  tynnest: x %.0f y %.0f z %.0f  %.2f mm" % (P[i, 0], P[i, 1], P[i, 2], tm[i]))
for x0 in range(5300, 7700, 400):
    mm = fin & (P[:, 0] >= x0) & (P[:, 0] < x0 + 400)
    if mm.any():
        print("  x %d-%d: min %.2f  p5 %.2f  (n %d)" % (x0, x0 + 400, tm[mm].min(), np.percentile(tm[mm], 5), mm.sum()))
