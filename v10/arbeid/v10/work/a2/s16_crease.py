"""Knekker mellom nabotrekanter paa skrogsiden rundt DWL (x 1500-6500, z -300..300)."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import common as CM
S = 30.0
for path in sys.argv[1:]:
    V, F = CM.weld(CM.load_raw(path))
    fn, area = CM.face_normals(V, F)
    c = V[F].mean(1)
    X = c[:, 0] * S; Z = c[:, 2] * S - 1400.0; Y = np.abs(c[:, 1]) * S
    sel = (X > 1500) & (X < 6500) & (Z > -300) & (Z < 300) & (Y > 300) & (np.abs(fn[:, 1]) > 0.3) & (area > 1e-12)
    idx = np.where(sel)[0]
    Fs = F[idx]
    E = np.concatenate([Fs[:, [0, 1]], Fs[:, [1, 2]], Fs[:, [2, 0]]])
    E.sort(axis=1)
    t = np.tile(np.arange(len(idx)), 3)
    key = E[:, 0] * (len(V) + 1) + E[:, 1]
    o = np.argsort(key)
    k2, t2 = key[o], t[o]
    same = k2[1:] == k2[:-1]
    a, b = t2[:-1][same], t2[1:][same]
    na, nb = fn[idx[a]], fn[idx[b]]
    ang = np.degrees(np.arccos(np.clip((na * nb).sum(1), -1, 1)))
    zm = 0.5 * (Z[idx[a]] + Z[idx[b]])
    near = np.abs(zm) < 50
    print(f"{os.path.basename(path)}: kanter {len(ang)}, >2 gr {np.mean(ang > 2)*100:.1f} %, >5 gr {np.mean(ang > 5)*100:.2f} %;  "
          f"av knekkene >2 gr ligger {np.mean(near[ang > 2])*100 if (ang > 2).any() else 0:.0f} % innen +-50 mm av DWL; maks {ang.max():.1f} gr")
