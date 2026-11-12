"""Preliminary underwater silhouette metric, IMG_9388 only, refined camera (camfit9388 start 1).
Signed horizontal offset model - photo (outward positive) on the rows where the
automatic red-region trace follows the true hull edge (right 860-960, left 880-955)."""
import sys, json
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/undervann/py")
import numpy as np
from PIL import Image, ImageDraw
import uw, candidates as K
P_CAM = [-1242.41, -4.06, 23.85, -2.98, 2.63, 0.35, 1705.58]
cam = uw.cam_from(P_CAM, "IMG_9388")
t = json.load(open(uw.OUT + "/traces/t9388_auto.json"))
L = np.array(t["uw_left_auto"]); R = np.array(t["uw_right_auto"])
L = L[(L[:, 0] >= 880) & (L[:, 0] <= 955)]; R = R[(R[:, 0] >= 860) & (R[:, 0] <= 960)]
res = {}
img = Image.fromarray(uw.photo("IMG_9388")); d = ImageDraw.Draw(img)
cols = {"today": (0, 230, 255), "B_dead_aft": (255, 255, 0), "F_dead_aft_n3.0": (255, 0, 255), "C_dead_aft_n2.6": (0, 255, 0)}
for k in cols:
    if k == "F_dead_aft_n3.0":
        K.set_tables(dead=K.CANDS["B_dead_aft"]["dead"], nexp=[(0.00, 2.4), (0.15, 2.9), (0.35, 3.0), (0.60, 3.0), (0.80, 2.9), (1.00, 2.8)])
    else:
        K.set_tables(**K.CANDS[k])
    V, F = uw.hull_mesh()
    rows = np.arange(0, 1100, 2.0)
    lo, hi, dlo, dhi = uw.row_extents(cam, V, F, rows)
    el = L[:, 1] - np.interp(L[:, 0], rows, lo)          # outward positive (model further left)
    er = np.interp(R[:, 0], rows, hi) - R[:, 1]
    sl = np.interp(L[:, 0], rows, dlo) / cam.f; sr = np.interp(R[:, 0], rows, dhi) / cam.f   # mm per px
    e = np.r_[el, er]; emm = np.r_[el * sl, er * sr]
    res[k] = dict(mean_px=float(e.mean()), rms_px=float(np.sqrt((e ** 2).mean())), mean_mm=float(emm.mean()),
                  rms_mm=float(np.sqrt((emm ** 2).mean())), left_mean_px=float(el.mean()), right_mean_px=float(er.mean()),
                  lowest_row=float(rows[np.isfinite(lo)].max()))
    for r_, a, b in zip(rows, lo, hi):
        if np.isfinite(a) and r_ > 600:
            d.point((a, r_), fill=cols[k]); d.point((b, r_), fill=cols[k])
    print(k, json.dumps({kk: round(vv, 1) for kk, vv in res[k].items()}))
for p in np.r_[L, R]:
    d.ellipse([p[1] - 2, p[0] - 2, p[1] + 2, p[0] + 2], outline=(255, 128, 0))
img.crop((150, 600, 1150, 1100)).save(uw.OUT + "/prelim_9388_overlay.png")
uw.save_json(dict(camera=P_CAM, rows_left=[880, 955], rows_right=[860, 960], results=res), uw.OUT + "/prelim_metric_9388.json")
