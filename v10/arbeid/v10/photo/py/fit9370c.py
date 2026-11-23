import json, csv, numpy as np
from scipy.optimize import least_squares
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
REPO = r"C:/Users/stig/Documents/GitHub/HR26-modell"
rows = list(csv.DictReader(open(f"{REPO}/data/hull_stations.csv")))
xs = np.array([float(r["x_from_bow_mm"]) for r in rows]); zs = np.array([float(r["strake_z_mm"]) for r in rows]); hb = np.array([float(r["deck_half_breadth_mm"]) for r in rows])
SO = np.array([(7300.0, 995.0), (7400.0, 968.0), (7500.0, 944.0), (7600.0, 916.0), (7700.0, 890.0), (7750.0, 866.0), (7800.0, 835.0), (7820.0, 812.0), (7840.0, 773.0), (7860.0, 730.0), (7880.0, 650.0), (7891.0, 605.0)])
def hbf(x):
    return np.where(x < 7300, np.interp(x, xs, hb), np.interp(x, SO[:, 0], SO[:, 1]))
st = np.array(json.load(open(f"{D}/m9370_strake.json"))["strake"])
old = np.array(json.load(open(f"{D}/m9370_lines.json"))["strake"])
extra = old[(old[:, 0] >= 906) & (old[:, 0] <= 982)]
extra = extra[np.abs(extra[:, 3] - np.interp(extra[:, 0], [906, 982], [1241.0, 1233.5])) < 2.5]
S = np.r_[st[:, [0, 3]], extra[:, [0, 3]]]; S = S[S[:, 0] >= 160]
outl = json.load(open(f"{D}/m9370_outl.json"))
stem = np.array(outl["stem"]); stem = stem[(stem[:, 1] >= 1236) & (stem[:, 1] <= 1322)]
tr = np.array(outl["transom"]); tr = tr[(tr[:, 0] > 968) & (tr[:, 1] <= 1250) & (tr[:, 1] >= 1214)]
zz = np.linspace(100, 1150, 400); stem_m = np.c_[1008.0 * (1 - (zz / 1204.0) ** (1 / 1.3)), 0 * zz, zz]
zt = np.linspace(300, 935, 300); tr_m = np.c_[7806.0 + 0.146 * zt, 0 * zt, zt]
xk = np.linspace(150, 7860, 800); strake_m = np.c_[xk, hbf(xk) - 25.0, np.interp(xk, xs, zs)]
head = np.array([[0.0, 0.0, 1204.0]]); head_px = np.array([150.8, 1222.3])


def proj(p, P):
    rho, su, sv, u0, v0, th, ph = p
    t, f = np.radians(th), np.radians(ph)
    a = (P[:, 0] * np.cos(t) + P[:, 1] * np.sin(t)) / su
    up = P[:, 2] * np.cos(f) - (-P[:, 0] * np.sin(t) + P[:, 1] * np.cos(t)) * np.sin(f)
    b = -up / sv
    c, s = np.cos(np.radians(rho)), np.sin(np.radians(rho))
    return np.c_[u0 + c * a - s * b, v0 + s * a + c * b]


def cres(obs, mp):
    return np.sqrt(((obs[:, None, :] - mp[None, :, :]) ** 2).sum(-1)).min(1)


def resid(p, fix=None):
    if fix is not None:
        p = np.array(p); p[list(fix)] = list(fix.values())
    r = [3.0 * (proj(p, head)[0] - head_px), cres(stem, proj(p, stem_m)) / np.sqrt(len(stem) / 50),
         cres(tr, proj(p, tr_m)) / np.sqrt(len(tr) / 20), cres(S, proj(p, strake_m)) / np.sqrt(len(S) / 100)]
    return np.concatenate([np.ravel(x) for x in r])


best = None
for th0 in (-10, -5, 0, 5, 10):
    for ph0 in (0, 5, 10):
        p0 = [-1.8, 9.6, 9.6, 160, 1352, th0, ph0]
        s = least_squares(resid, p0, x_scale=[1, .5, .5, 5, 5, 2, 2], bounds=([-10, 5, 5, 0, 1200, -40, -20], [10, 15, 15, 400, 1500, 40, 30]))
        if best is None or s.cost < best.cost:
            best = s
p = best.x
print("rho %.2f su %.3f sv %.3f (sv/su %.3f) u0 %.1f v0 %.1f yaw %.2f elev %.2f  cost %.1f" % (p[0], p[1], p[2], p[2] / p[1], p[3], p[4], p[5], p[6], best.cost))
for nm, obs, mod in (("stem", stem, stem_m), ("transom", tr, tr_m), ("strake", S, strake_m)):
    r = cres(obs, proj(p, mod)); print(nm, "rms %.2f max %.2f px" % (np.sqrt((r ** 2).mean()), r.max()))
print("head", proj(p, head)[0] - head_px)
mp = proj(p, strake_m)
for u in range(170, 990, 60):
    i = np.argmin(abs(S[:, 0] - u)); j = np.argmin(abs(mp[:, 0] - S[i, 0]))
    print("  u %4d x~%5.0f obs %.1f model %.1f diff %+.1f px" % (S[i, 0], xk[j], S[i, 1], mp[j, 1], S[i, 1] - mp[j, 1]))
json.dump({"p": p.tolist(), "names": ["rho", "su", "sv", "u0", "v0", "yaw", "elev"]}, open(f"{D}/fit9370c.json", "w"))
