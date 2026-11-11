import sys, json, numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/py")
from cam import generic_rot, pinhole
from cam9370 import inv as inv70, hbf
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
m = json.load(open(f"{D}/m9388.json"))
Lf = np.array(m["left"]); Rt = np.array(m["right"])
Lf = Lf[Lf[:, 0] <= 600]; Rt = Rt[Rt[:, 0] <= 600]
obsL = np.c_[Lf[:, 1], Lf[:, 0]]; obsR = np.c_[Rt[:, 1], Rt[:, 0]]
so = np.load(f"{D}/model_strake_outer.npy"); so = so[~np.isnan(so[:, 1])]
so = so[so[:, 0] >= 300]
SL = np.c_[so[:, 0], so[:, 1], so[:, 2]]; SR = np.c_[so[:, 0], -so[:, 1], so[:, 2]]
zz = np.linspace(250, 1150, 60); stem3 = np.c_[1008.0 * (1 - (zz / 1204.0) ** (1 / 1.3)), 0 * zz, zz]
keel = np.array([[4894.0, 0, -1400.0]]); keel_px = np.array([656.0, 1302.0])
# boot-top height near bow from IMG_9370
xz = inv70(np.array([[260.0, 1325.5], [300.0, 1326.7]]), lambda x, z: 0.35 * float(hbf(x)))
print("boot-top top near bow from 9370 (x,z):", xz.round(0))
zbt = float(xz[:, 1].mean())
btstem = np.array([[1008.0 * (1 - (zbt / 1204.0) ** (1 / 1.3)), 0, zbt]]); btstem_px = np.array([648.0, 512.0])
W, H = 1500, 2000


def cam_of(p):
    f, Xc, Yc, Zc, yaw, pitch, roll = p
    fwd = np.array([np.cos(np.radians(pitch)) * np.cos(np.radians(yaw)), np.cos(np.radians(pitch)) * np.sin(np.radians(yaw)), np.sin(np.radians(pitch))])
    R = generic_rot(fwd, roll=roll)
    return R, np.array([Xc, Yc, Zc]), f


def P(p, X):
    R, C, f = cam_of(p)
    uv, z = pinhole(X, R, C, f, W / 2, H / 2)
    return uv


def cres(obs, mp):
    return np.sqrt(((obs[:, None, :] - mp[None, :, :]) ** 2).sum(-1)).min(1)


def resid(p):
    r = [cres(obsL, P(p, SL)) / np.sqrt(len(obsL) / 60), cres(obsR, P(p, SR)) / np.sqrt(len(obsR) / 60),
         (P(p, stem3)[:, 0] - 647.5) / np.sqrt(len(stem3) / 10),
         0.5 * (P(p, keel)[0] - keel_px), 0.7 * (P(p, btstem)[0] - btstem_px)]
    return np.concatenate([np.ravel(a) for a in r])


best = None
for f0 in (1500, 2200, 3000):
    for d0 in (-2500, -4000, -6000):
        for z0 in (-400, 0, 400):
            p0 = [f0, d0, 0, z0, 0, 5, 0]
            try:
                s = least_squares(resid, p0, bounds=([800, -15000, -1500, -2000, -20, -30, -10], [6000, -300, 1500, 2500, 20, 40, 10]), x_scale=[200, 300, 50, 100, 1, 1, 1])
            except Exception as e:
                continue
            if best is None or s.cost < best.cost:
                best = s
p = best.x
print("f %.0f  C=(%.0f, %.0f, %.0f)  yaw %.2f pitch %.2f roll %.2f  cost %.1f" % (*p, best.cost))
for nm, o, X in (("L", obsL, SL), ("R", obsR, SR)):
    r = cres(o, P(p, X)); print(nm, "rms %.2f max %.2f" % (np.sqrt((r ** 2).mean()), r.max()))
print("stem u", P(p, stem3)[::10, 0].round(1), "keel", P(p, keel)[0].round(1), "bt stem", P(p, btstem)[0].round(1))
json.dump({"p": p.tolist(), "zbt": zbt}, open(f"{D}/fit9388.json", "w"))
# which x does each image row of strake correspond to
pl = P(p, SL)
for v in (0, 100, 200, 300, 400, 500, 600, 700, 800):
    i = np.argmin(abs(pl[:, 1] - v)); print("row", v, "model strake x %.0f y %.0f z %.0f at u %.1f" % (SL[i, 0], SL[i, 1], SL[i, 2], pl[i, 0]))
