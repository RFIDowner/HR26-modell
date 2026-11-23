"""STL vs formula as signed normal distance (robust near the flat bottom)."""
import sys, math, json
import numpy as np
HERE = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/verify-sections"
sys.path.insert(0, HERE); sys.path.insert(0, r"C:/Users/stig/Documents/GitHub/HR26-modell")
from v_stl_lib import load_stl, rot_z, slice_x, outer_y_of_z
from hr26 import curves as C, params as P
ANG = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
T = rot_z(load_stl(r"C:/Users/stig/Documents/GitHub/HR26-modell/export/stl/01_skrog.stl"), -ANG)
V = T.reshape(-1, 3); T[:, :, 1] -= 0.5 * (V[:, 1].max() + V[:, 1].min())
F = T * P.SCALE; F[:, :, 2] -= 1400.0
kt = F.reshape(-1, 3); kt = kt[kt[:, 2] < -1390.0]
F[:, :, 0] += 0.5 * ((P.KEEL_LE_TIP - kt[:, 0].min()) + (P.KEEL_TE_TIP - kt[:, 0].max()))

def sdist(x, ys, zs_):
    sec = np.array(C.section(x, n=3000))
    out = np.full(len(ys), np.nan)
    for i, (y, z) in enumerate(zip(ys, zs_)):
        if not np.isfinite(y): continue
        d = np.hypot(sec[:, 0] - y, sec[:, 1] - z); j = np.argmin(d)
        yf = np.interp(z, sec[:, 1], sec[:, 0], left=np.nan, right=np.nan)
        s = 1.0 if (np.isfinite(yf) and y >= yf) else -1.0
        out[i] = s * d[j]
    return out

xs = json.load(open(HERE + "/v_formula.json"))["loft_x"]
mids = [0.5 * (a + b) for a, b in zip(xs[:-1], xs[1:])]
zg = np.arange(-560.0, 1250.0, 4.0)
res = []
for x in sorted(xs + mids):
    if x < 150 or x > 7700: continue
    seg = slice_x(F, x)
    yp = outer_y_of_z(seg, zg, +1); ym = -outer_y_of_z(seg, zg, -1)
    zb, zk, zs = C.bottom_z(x), C.strake_z(x), C.sheer_z(x)
    lo = max(zb, -560.0) + 8.0
    # keel region (3380..5800 + fillet) excluded below z=-300 to avoid the keel/fillet
    under = (zg > lo) & (zg < -2)
    if 3200 < x < 5900: under &= zg > -330
    top = (zg > 2) & (zg < zk - 110)
    res_x = {}
    for nm, m in (("under", under), ("top", top)):
        dd = []
        for y in (yp, ym):
            d = sdist(x, y[m], zg[m]); dd.append(d)
        d = np.nanmean(np.vstack(dd), axis=0) if len(dd[0]) else np.array([np.nan])
        if np.all(~np.isfinite(d)):
            res_x[nm] = (np.nan, np.nan); continue
        j = np.nanargmax(np.abs(d)); res_x[nm] = (float(d[j]), float(zg[m][j]))
    tag = "loft" if x in xs else "mid "
    res.append((x, res_x))
    print(f"{tag} x={x:7.1f}  under {res_x['under'][0]:7.1f} @z {res_x['under'][1]:6.0f}   top {res_x['top'][0]:7.1f} @z {res_x['top'][1]:6.0f}")
json.dump(res, open(HERE + f"/v_stl_normal_{int(ANG)}.json", "w"), default=float)
