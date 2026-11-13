"""Fenderlistens bue over akterspeilet, maalt paa IMG_9391 (13.11.2026, kveld).

Kameraet loeses som i cam9391.py (vannlinjestripens to kanter paa akterspeilet,
venstre silhuett over stripen, roret), men listen er ikke lenger en vannrett
linje: z(y) = z_c - a * (y / Y)^2 over akterspeilet, og hele sporet (u 120-998)
brukes. Hjoernene (|y| = Y) ankres svakt til listens hoyde paa siden
(curves.strake_z, maalt fra siden), saa a blir buen opp mot midten.

Kjoeres fra denne mappa: python liste9391.py
"""
import json
import numpy as np
from scipy.optimize import least_squares
import common as c, uwlib as U
import cam9391 as K

Y = 560.0                                   # listens halvbredde der buen moeter hjoernet
Z_SIDE = float(c.C.strake_z(7850.0))        # listens hoyde paa siden ved akterspeilet
st_all = np.array(json.load(open(c.W + "/out/t9391.json"))["strake"])
ST = np.c_[st_all[:, 0], 0.5 * (st_all[:, 1] + st_all[:, 2])]
ys = np.linspace(-Y, Y, 113)


def strake3(zc, a):
    z = zc - a * (ys / Y) ** 2
    return np.c_[[U.transom_x(zz, y) + 13.0 for zz, y in zip(z, ys)], ys, z]


def res(q, parts=False, corner_sig=25.0):
    K.st_c = ST
    K.STRAKE3 = strake3(q[9], q[10])
    g = K.residuals(q[:9], True)
    g["prior"] = np.array([(q[6] - 1495.0) / 10.0, q[8] / 5.0,
                           (q[9] - q[10] - Z_SIDE) / corner_sig]) * 3.0
    if parts:
        return g
    return np.concatenate([v / np.sqrt(max(len(v), 1) / 30.0) if k != "prior" else v
                           for k, v in g.items()])


def solve(corner_sig=25.0):
    p0 = json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"]
    best = None
    for zc0, a0 in ((805.0, 0.0), (850.0, 50.0), (760.0, 0.0)):
        s = list(p0[:9]) + [zc0, a0]
        r = least_squares(lambda q: res(q, False, corner_sig), s,
                          bounds=([8300, -1500, -1300, 160, -20, -15, 1100, 0, -100, 500, -100],
                                  [14000, 1500, 1500, 190, 30, 15, 2200, 400, 100, 1100, 300]),
                          x_scale=[200, 50, 100, 1, 1, 1, 50, 20, 10, 20, 10],
                          loss="soft_l1", f_scale=4.0, max_nfev=800)
        if best is None or r.cost < best.cost:
            best = r
    return best


if __name__ == "__main__":
    out = {}
    for sig in (25.0, 1000.0):
        b = solve(sig)
        g = res(b.x, True, sig)
        q = b.x
        print("hjoerneanker sd %4.0f: senter z %.0f, bue a %.0f mm (hjoerner %.0f, siden %.0f) | rms %s"
              % (sig, q[9], q[10], q[9] - q[10], Z_SIDE, {k: round(K.rms(v), 2) for k, v in g.items()}))
        out["sig%d" % int(sig)] = dict(p=q, zc=q[9], a=q[10], rms={k: K.rms(v) for k, v in g.items()})
    # samme med vannrett liste over hele bredden, til sammenligning
    def res0(q):
        K.st_c = ST
        K.STRAKE3 = strake3(q[9], 0.0)
        g = K.residuals(q[:9], True)
        g["prior"] = np.array([(q[6] - 1495.0) / 10.0, q[8] / 5.0]) * 3.0
        return np.concatenate([v / np.sqrt(max(len(v), 1) / 30.0) if k != "prior" else v for k, v in g.items()])
    p0 = json.load(open(c.W + "/out/cam9391.json"))["zc5"]["p"]
    r0 = least_squares(res0, list(p0[:9]) + [805.0],
                       bounds=([8300, -1500, -1300, 160, -20, -15, 1100, 0, -100, 500],
                               [14000, 1500, 1500, 190, 30, 15, 2200, 400, 100, 1100]),
                       x_scale=[200, 50, 100, 1, 1, 1, 50, 20, 10, 20], loss="soft_l1", f_scale=4.0, max_nfev=800)
    K.STRAKE3 = strake3(r0.x[9], 0.0)
    g0 = K.residuals(r0.x[:9], True)
    print("vannrett liste (som i dag):  z %.0f | rms %s" % (r0.x[9], {k: round(K.rms(v), 2) for k, v in g0.items()}))
    out["level"] = dict(p=r0.x, rms={k: K.rms(v) for k, v in g0.items()})
    c.save_json(out, c.W + "/out/liste9391.json")
