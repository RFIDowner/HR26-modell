"""Fitted orthographic camera for IMG_9370 + inverse mapping onto a surface y = yfun(x, z)."""
import json, csv, numpy as np
from scipy.optimize import least_squares
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
REPO = r"C:/Users/stig/Documents/GitHub/HR26-modell"
P9370 = np.array(json.load(open(f"{D}/fit9370c.json"))["p"])
rows = list(csv.DictReader(open(f"{REPO}/data/hull_stations.csv")))
XS = np.array([float(r["x_from_bow_mm"]) for r in rows]); ZS = np.array([float(r["strake_z_mm"]) for r in rows]); HB = np.array([float(r["deck_half_breadth_mm"]) for r in rows])
SO = np.array([(7300.0, 995.0), (7400.0, 968.0), (7500.0, 944.0), (7600.0, 916.0), (7700.0, 890.0), (7750.0, 866.0), (7800.0, 835.0), (7820.0, 812.0), (7840.0, 773.0), (7860.0, 730.0), (7880.0, 650.0), (7891.0, 605.0)])
DEZ = np.array([(0.0, 1204.0), (1000.0, 1204.0), (2000.0, 1200.0), (2500.0, 1175.0), (3000.0, 1150.0), (3750.0, 1122.0), (4200.0, 1115.0), (4500.0, 1105.0), (5000.0, 1095.0), (5500.0, 1085.0), (6000.0, 1080.0), (6500.0, 1075.0), (7000.0, 1056.0), (7200.0, 1040.0), (7400.0, 1020.0), (7600.0, 992.0), (7800.0, 962.0), (7950.0, 940.0)])


def hbf(x):
    x = np.asarray(x, float)
    return np.where(x < 7300, np.interp(x, XS, HB), np.interp(x, SO[:, 0], SO[:, 1]))


def sheer(x):
    return np.interp(x, DEZ[:, 0], DEZ[:, 1])


def strake(x):
    return np.interp(x, XS, ZS)


def proj(P, p=P9370):
    rho, su, sv, u0, v0, th, ph = p
    t, f = np.radians(th), np.radians(ph)
    a = (P[:, 0] * np.cos(t) + P[:, 1] * np.sin(t)) / su
    up = P[:, 2] * np.cos(f) - (-P[:, 0] * np.sin(t) + P[:, 1] * np.cos(t)) * np.sin(f)
    b = -up / sv
    c, s = np.cos(np.radians(rho)), np.sin(np.radians(rho))
    return np.c_[u0 + c * a - s * b, v0 + s * a + c * b]


def inv(uv, yfun):
    """image (u,v) -> (x, z) on surface y=yfun(x,z)."""
    out = []
    for u, v in np.atleast_2d(uv):
        def r(q):
            x, z = q
            return proj(np.array([[x, yfun(x, z), z]]))[0] - [u, v]
        q0 = [(u - P9370[3]) * P9370[1], (P9370[4] - v) * P9370[2]]
        s = least_squares(r, q0)
        out.append(s.x)
    return np.array(out)
