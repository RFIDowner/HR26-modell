"""LSQ fit of side photo: image = R(rho) * diag(1/su, -1/sv) * (x, z) + (u0, v0); constraints: stem head, stem profile,
transom profile, strake curve (drawing). Curve terms use nearest-point distances (resampled model curves)."""
import json, csv, numpy as np
from scipy.optimize import least_squares
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
REPO = r"C:/Users/stig/Documents/GitHub/HR26-modell"
rows = list(csv.DictReader(open(f"{REPO}/data/hull_stations.csv")))
xs = np.array([float(r["x_from_bow_mm"]) for r in rows]); zs = np.array([float(r["strake_z_mm"]) for r in rows])
st = np.array(json.load(open(f"{D}/m9370_strake.json"))["strake"])
old = np.array(json.load(open(f"{D}/m9370_lines.json"))["strake"])
extra = old[(old[:, 0] >= 906) & (old[:, 0] <= 982)]
extra = extra[np.abs(extra[:, 3] - np.interp(extra[:, 0], [906, 982], [1241.0, 1233.5])) < 2.5]
S = np.r_[st[:, [0, 3]], extra[:, [0, 3]]]
S = S[(S[:, 0] >= 160)]
outl = json.load(open(f"{D}/m9370_outl.json"))
stem = np.array(outl["stem"]); stem = stem[(stem[:, 1] >= 1236) & (stem[:, 1] <= 1322)]
tr = np.array(outl["transom"]); tr = tr[(tr[:, 0] > 968) & (tr[:, 1] <= 1250) & (tr[:, 1] >= 1214)]
# model curves (x, z)
zz = np.linspace(100, 1150, 400); stem_m = np.c_[1008.0 * (1 - (zz / 1204.0) ** (1 / 1.3)), zz]
zt = np.linspace(300, 935, 300); tr_m = np.c_[7806.0 + 0.146 * zt, zt]
xk = np.linspace(150, 7850, 800); strake_m = np.c_[xk, np.interp(xk, xs, zs)]
head = np.array([0.0, 1204.0]); head_px = np.array([150.8, 1222.3])


def proj(p, P):
    rho, su, sv, u0, v0 = p
    c, s = np.cos(np.radians(rho)), np.sin(np.radians(rho))
    a = P[:, 0] / su; b = -P[:, 1] / sv
    return np.c_[u0 + c * a - s * b, v0 + s * a + c * b]


def curve_res(obs, model_px):
    d = np.sqrt(((obs[:, None, :] - model_px[None, :, :]) ** 2).sum(-1))
    return d.min(1)


def resid(p, w=(3.0, 1.0, 1.0, 1.0)):
    r = [w[0] * (proj(p, head[None])[0] - head_px)]
    r.append(w[1] * curve_res(stem, proj(p, stem_m)) / np.sqrt(len(stem) / 50))
    r.append(w[2] * curve_res(tr, proj(p, tr_m)) / np.sqrt(len(tr) / 20))
    r.append(w[3] * curve_res(S, proj(p, strake_m)) / np.sqrt(len(S) / 100))
    return np.concatenate([np.ravel(x) for x in r])


p0 = [0.0, 9.5, 10.5, 150.8, 1222.3 + 1204 / 10.5]
sol = least_squares(resid, p0, x_scale=[1, 0.5, 0.5, 5, 5])
p = sol.x
print("rho %.2f deg, su %.3f mm/px, sv %.3f mm/px (sv/su %.3f), u0 %.1f v0 %.1f" % tuple(list(p[:3]) + [p[2] / p[1]] + list(p[3:])))
print("head res", proj(p, head[None])[0] - head_px)
for nm, obs, mod in (("stem", stem, stem_m), ("transom", tr, tr_m), ("strake", S, strake_m)):
    r = curve_res(obs, proj(p, mod)); print(nm, "n", len(obs), "rms %.2f max %.2f px" % (np.sqrt((r ** 2).mean()), r.max()))
# signed strake residual along u
mp = proj(p, strake_m)
for u in range(170, 990, 60):
    i = np.argmin(abs(S[:, 0] - u)); j = np.argmin(abs(mp[:, 0] - S[i, 0]))
    print("  u %4d obs v %.1f model v %.1f -> diff %+.1f px (%+.0f mm)" % (S[i, 0], S[i, 1], mp[j, 1], S[i, 1] - mp[j, 1], -(S[i, 1] - mp[j, 1]) * p[2]))
json.dump({"p": p.tolist()}, open(f"{D}/fit9370.json", "w"))
# fixed-anisotropy alternative: sv = su (isotropic)
def resid_iso(q):
    return resid([q[0], q[1], q[1], q[2], q[3]])
s2 = least_squares(resid_iso, [p[0], p[1], p[3], p[4]])
q = s2.x
print("ISO: rho %.2f su=sv %.3f, cost %.1f vs aniso cost %.1f" % (q[0], q[1], s2.cost, sol.cost))
for nm, obs, mod in (("stem", stem, stem_m), ("transom", tr, tr_m), ("strake", S, strake_m)):
    r = curve_res(obs, proj([q[0], q[1], q[1], q[2], q[3]], mod)); print("  ISO", nm, "rms %.2f max %.2f px" % (np.sqrt((r ** 2).mean()), r.max()))
