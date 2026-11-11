"""Render the 4 photo pairs with the cameras in cam_*.json (dev check)."""
import sys, json
sys.path.insert(0, "..")
import numpy as np, score as S
from PIL import Image
V = np.load("V_fine.npy"); F = np.load("F_fine.npy")
fn, *_ = S.face_geom(V, F)
crops = {"9388": (60, 250, 1440, 1460), "9391": (0, 0, 1500, 1700), "9370": (60, 1080, 1038, 1420), "9389": (100, 0, 2000, 1080)}
titles = {"9388": "bow head-on, on land", "9391": "transom from astern, on land", "9370": "side afloat (port)", "9389": "3/4 from the starboard bow, low"}
out = []
for k in ("9388", "9391", "9370", "9389"):
    p = json.load(open(f"cam_{k}.json"))
    pv = dict(file=f"IMG_{k}.jpeg", title=titles[k], C=p[:3], yaw=p[3], pitch=p[4], roll=p[5], f=p[6], crop=crops[k])
    im = S.photo_pair(pv, V, F, fn, "C:/Users/stig/Documents/Seilbåt", 795, 450)
    out.append(im)
    print(k, np.round(p, 2).tolist())
sheet = Image.new("RGB", (1600, 2 * 456), (255, 255, 255))
for i, im in enumerate(out):
    sheet.paste(im, (4 + (i % 2) * 800, (i // 2) * 456))
sheet.save("pairs.png")
