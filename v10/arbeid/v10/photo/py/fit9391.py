import sys, json, numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/py")
from cam import generic_rot, pinhole
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
S = np.array(json.load(open(f"{D}/m9391_strake.json"))["strake"])
S = S[((S[:, 0] <= 560) | ((S[:, 0] >= 700) & (S[:, 0] <= 1240)))]
obsS = np.c_[S[:, 0], S[:, 3]]
# thin band right side: dark threshold included shadow; use top edge + 13 as centre for u>=950
obsS[:, 1] = np.where(S[:, 0] >= 950, S[:, 1] + 13.0, S[:, 3])
o = np.load(f"{D}/model_z804_stern.npy")
o = o[np.argsort(o[:, 1])]
# keep envelope: x should be max-ish smooth; drop points far below running max of neighbours
keep = []
for i in range(len(o)):
    nb = o[max(0, i - 2):i + 3, 0]
    if o[i, 0] >= np.median(nb) - 15:
        keep.append(i)
o = o[keep]
o = o[np.abs(o[:, 1]) <= 760]
yy = np.linspace(o[:, 1].min(), o[:, 1].max(), 300)
strake3 = np.c_[np.interp(yy, o[:, 1], o[:, 0]) - 25.0, yy, np.full_like(yy, 804.0)]
bt_obs = np.array([[u, 656.5] for u in range(320, 1000, 40)])
rud3 = np.array([[8150.0, 0, -1094.0]]); rud_px = np.array([701.0, 1576.0])
W, H = 1500, 2000


def tx(z, y):
    R = 3050.0; sag = R - np.sqrt(R * R - y * y); return 7806 + 0.146 * z - sag * np.sqrt(1 + 0.146 ** 2)


def cam(p):
    f, Xc, Yc, Zc, yaw, pitch, roll, zbt = p
    fwd = np.array([np.cos(np.radians(pitch)) * np.cos(np.radians(yaw)), np.cos(np.radians(pitch)) * np.sin(np.radians(yaw)), np.sin(np.radians(pitch))])
    return generic_rot(fwd, roll=roll), np.array([Xc, Yc, Zc]), f


def P(p, X):
    R, C, f = cam(p)
    return pinhole(X, R, C, f, W / 2, H / 2)[0]


def cres(obs, mp):
    return np.sqrt(((obs[:, None, :] - mp[None, :, :]) ** 2).sum(-1)).min(1)


def resid(p):
    zbt = p[7]
    yb = np.linspace(-330, 330, 60)
    bt3 = np.c_[tx(zbt, yb), yb, np.full_like(yb, zbt)]
    r = [cres(obsS, P(p, strake3)) / np.sqrt(len(obsS) / 80), cres(bt_obs, P(p, bt3)), 2.0 * (P(p, rud3)[0] - rud_px)]
    return np.concatenate([np.ravel(a) for a in r])


best = None
for f0 in (1500, 2000):
    for d0 in (9200, 9800, 10800):
        for z0 in (-300, 100):
            p0 = [f0, d0, 0, z0, 180, 10, 0, 120]
            try:
                s = least_squares(resid, p0, bounds=([900, 8300, -800, -1200, 160, -20, -10, -50], [5000, 16000, 800, 1500, 200, 45, 10, 300]), x_scale=[200, 300, 50, 100, 1, 1, 1, 20])
            except Exception as e:
                print("fail", e); continue
            if best is None or s.cost < best.cost:
                best = s
p = best.x
print("f %.0f C=(%.0f,%.0f,%.0f) yaw %.2f pitch %.2f roll %.2f zbt %.0f cost %.1f" % (*p, best.cost))
r = cres(obsS, P(p, strake3)); print("strake rms %.2f max %.2f" % (np.sqrt((r ** 2).mean()), r.max()))
print("rudder", P(p, rud3)[0].round(1))
yb = np.linspace(-330, 330, 5); print("bt", P(p, np.c_[tx(p[7], yb), yb, np.full_like(yb, p[7])]).round(1))
json.dump({"p": p.tolist()}, open(f"{D}/fit9391.json", "w"))
