"""Kantene naer modellens dekkskant i de rettede stripene (kd_rect.py).

For hver x: luminansen opp langs z paa skrogsiden, glattet; de sterkeste
kantene (lys under -> moerkere over = 'ned', omvendt = 'opp') i vinduet
z = sheer_z(x) - 90 ... + 60. Skriver tabellen og ../out/kd_edges_<navn>.json.

  python ../../../../tools/memcap.py --gb 3 -- python kd_edges.py rect.npz navn [x0 x1 dx]
"""
import sys

import numpy as np
from scipy.ndimage import gaussian_filter

import common as c
from hr26 import curves as C


def edges(npz, x0=3000.0, x1=7800.0, dx=50.0, lo=-90.0, hi=60.0, sig=(1.2, 2.0)):
    d = np.load(npz)
    x, z, R = d["x"], d["z"], d["rgb"]
    Lm = gaussian_filter(R.mean(2), sig)
    g = np.gradient(Lm, axis=0) / (z[1] - z[0])        # dL/dz (per mm)
    out = []
    for xx in np.arange(x0, x1 + 0.1, dx):
        i = int(np.argmin(np.abs(x - xx)))
        zs = C.sheer_z(xx)
        m = (z >= zs + lo) & (z <= zs + hi)
        gi, zi = g[m, i], z[m]
        res = dict(x=float(xx), sheer=float(zs), strake=float(C.strake_z(xx)))
        for key, sgn in (("ned", -1.0), ("opp", 1.0)):
            s = sgn * gi
            # lokale maksima, sortert
            pk = [k for k in range(1, len(s) - 1) if s[k] >= s[k - 1] and s[k] >= s[k + 1] and s[k] > 0.3]
            pk = sorted(pk, key=lambda k: -s[k])[:3]
            lst = []
            for k in pk:
                # subpiksel (parabel)
                a, b, cc = s[k - 1], s[k], s[k + 1]
                den = a - 2 * b + cc
                off = 0.5 * (a - cc) / den if den != 0 else 0.0
                zz = zi[k] + off * (z[1] - z[0])
                lst.append((round(float(zz - zs), 1), round(float(s[k]), 2)))
            res[key] = lst
        out.append(res)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    npz, name = a[0], a[1]
    kw = {}
    if len(a) >= 5:
        kw = dict(x0=float(a[2]), x1=float(a[3]), dx=float(a[4]))
    E = edges(npz, **kw)
    c.save_json(E, c.W + "/out/kd_edges_%s.json" % name)
    for r in E:
        print("x %5.0f sheer %5.0f | ned %-40s | opp %s" % (r["x"], r["sheer"], r["ned"], r["opp"]))
