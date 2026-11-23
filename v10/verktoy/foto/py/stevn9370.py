"""Stevnens vinkel og overheng maalt paa IMG_9370 (baaten flyter, nesten rett fra siden).

Kameraet (ortografisk, som fit9370c.py) stilles inn UTEN stevnen: stevnhodet,
akterspeilets linje og fenderlisten langs siden. Stevnens kant spores i
originalbildet (hvitt skrog mot fjell, blaa kanal) og projiseres tilbake paa
senterplanet y = 0. Skriver ut vinkel, rest fra rett linje og x ved noen hoyder.

Kjoeres fra denne mappa: python stevn9370.py
"""
import csv, json, math, sys
import numpy as np
from PIL import Image
from scipy.optimize import least_squares
import common as c

PH = c.REPO + "/v10/arbeid/v10/photo"
rows = list(csv.DictReader(open(c.REPO + "/data/hull_stations.csv")))
xs = np.array([float(r["x_from_bow_mm"]) for r in rows])
zs = np.array([float(r["strake_z_mm"]) for r in rows])
hb = np.array([float(r["deck_half_breadth_mm"]) for r in rows])
SO = np.array(c.P.STERN_OUTLINE)


def hbf(x):
    return np.where(x < 7300, np.interp(x, xs, hb), np.interp(x, SO[:, 0], SO[:, 1]))


st = np.array(json.load(open(PH + "/m9370_strake.json"))["strake"])
old = np.array(json.load(open(PH + "/m9370_lines.json"))["strake"])
extra = old[(old[:, 0] >= 906) & (old[:, 0] <= 982)]
extra = extra[np.abs(extra[:, 3] - np.interp(extra[:, 0], [906, 982], [1241.0, 1233.5])) < 2.5]
S = np.r_[st[:, [0, 3]], extra[:, [0, 3]]]
S = S[S[:, 0] >= 160]
outl = json.load(open(PH + "/m9370_outl.json"))
tr = np.array(outl["transom"])
tr = tr[(tr[:, 0] > 968) & (tr[:, 1] <= 1250) & (tr[:, 1] >= 1214)]
zt = np.linspace(300, 935, 300)
tr_m = np.c_[7806.0 + 0.146 * zt, 0 * zt, zt]
xk = np.linspace(150, 7860, 800)
strake_m = np.c_[xk, hbf(xk) - 25.0, np.interp(xk, xs, zs)]
head = np.array([[0.0, 0.0, 1204.0]])
head_px = np.array([150.8, 1222.3])


def proj(p, P):
    rho, su, sv, u0, v0, th, ph = p
    t, f = np.radians(th), np.radians(ph)
    a = (P[:, 0] * np.cos(t) + P[:, 1] * np.sin(t)) / su
    up = P[:, 2] * np.cos(f) - (-P[:, 0] * np.sin(t) + P[:, 1] * np.cos(t)) * np.sin(f)
    b = -up / sv
    cr, sr = np.cos(np.radians(rho)), np.sin(np.radians(rho))
    return np.c_[u0 + cr * a - sr * b, v0 + sr * a + cr * b]


def cres(obs, mp):
    return np.sqrt(((obs[:, None, :] - mp[None, :, :]) ** 2).sum(-1)).min(1)


def resid(p, w_head=3.0):
    r = [w_head * (proj(p, head)[0] - head_px),
         cres(tr, proj(p, tr_m)) / np.sqrt(len(tr) / 20),
         cres(S, proj(p, strake_m)) / np.sqrt(len(S) / 100)]
    return np.concatenate([np.ravel(x) for x in r])


def fit():
    best = None
    for th0 in (-5, 0, 5):
        for ph0 in (0, 5, 10):
            s = least_squares(resid, [-1.8, 9.6, 9.6, 160, 1352, th0, ph0],
                              x_scale=[1, .5, .5, 5, 5, 2, 2],
                              bounds=([-10, 5, 5, 0, 1200, -40, -20], [10, 15, 15, 400, 1500, 40, 30]))
            if best is None or s.cost < best.cost:
                best = s
    return best.x


def stem_trace():
    im = np.asarray(Image.open(c.SRC + "/../IMG_9370.jpeg").convert("RGB")).astype(float)
    B = im[..., 2]
    pts = []
    for v in range(1236, 1321):
        row = B[v, 130:320]
        ok = row > 195
        u = next((i for i in range(len(ok) - 6) if ok[i:i + 6].all()), None)
        if u is None or u < 3:
            continue
        a, b = row[u - 3], row[u + 3]
        mid = 0.5 * (a + b)
        seg = row[u - 3:u + 4]
        j = int(np.argmax(seg > mid))
        us = u - 3 + j - 1 + (mid - seg[j - 1]) / (seg[j] - seg[j - 1]) if j > 0 else u
        pts.append((130 + us, v))
    return np.array(pts, float)


def backproject(p, uv):
    """(u, v) -> (x, z) paa y = 0 (lineaert for et ortografisk kamera)."""
    e = proj(p, np.array([[0, 0, 0], [1, 0, 0], [0, 0, 1]], float))
    o, ex, ez = e[0], e[1] - e[0], e[2] - e[0]
    M = np.c_[ex, ez]
    return np.linalg.solve(M, (uv - o).T).T


if __name__ == "__main__":
    p = fit()
    print("kamera uten stevn: rho %.2f su %.3f sv %.3f yaw %.2f elev %.2f" % (p[0], p[1], p[2], p[5], p[6]))
    for nm, obs, mod in (("akterspeil", tr, tr_m), ("fenderlist", S, strake_m)):
        r = cres(obs, proj(p, mod))
        print("  %-10s rms %.2f px" % (nm, np.sqrt((r ** 2).mean())))
    uv = stem_trace()
    xz = backproject(p, uv)
    k, m = np.polyfit(xz[:, 1], xz[:, 0], 1)          # x = k z + m
    res = xz[:, 0] - (k * xz[:, 1] + m)
    ang = math.degrees(math.atan2(1.0, abs(k)))
    print("stevnen z %.0f..%.0f: %.1f grader fra vannrett, rest fra rett linje rms %.1f mm, maks %.1f mm"
          % (xz[:, 1].min(), xz[:, 1].max(), ang, res.std(), np.abs(res).max()))
    for z in (1100, 1000, 800, 600, 400, 200, 130, 0):
        print("  z %5d: x foto %6.0f   modell %6.0f" % (z, k * z + m, np.interp(-z, -np.array([c.C.bottom_z(t) for t in np.linspace(0, 1300, 1301)]), np.linspace(0, 1300, 1301))))
    print("laveste sporede punkt (vannflaten ved stevnen): z %.0f, x %.0f" % (xz[-1, 1], xz[-1, 0]))
    json.dump({"cam": p.tolist(), "k": k, "m": m, "angle_deg": ang, "rms_mm": float(res.std()),
               "xz": xz.tolist()}, open(c.W + "/out/stevn9370.json", "w"), indent=1)
