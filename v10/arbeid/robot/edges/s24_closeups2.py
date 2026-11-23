import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from render2 import render
T = np.load(OUT + "/ours_full.npy"); B = np.load(OUT + "/bambu_full_nostretch.npy")
B = B[B[:, :, 2].min(1) < 2300]
W = OUT + "/work"
cells = {
  "bow":   dict(az=-62, el=10, tgt_o=(520, 0, 1030), tgt_b=(520, 0, 1130), w=1800),
  "deck":  dict(az=-78, el=12, tgt_o=(3300, 1100, 1120), tgt_b=(3300, 950, 1260), w=1700),
  "front": dict(az=-35, el=20, tgt_o=(2330, 250, 1270), tgt_b=(1480, 250, 1330), w=1400),
  "stern": dict(az=218, el=18, tgt_o=(7550, 350, 960), tgt_b=(7480, 350, 1110), w=2100),
  "winch": dict(az=-125, el=22, tgt_o=(5850, 750, 1350), tgt_b=(5850, 650, 1400), w=1700),
}
for nm, c in cells.items():
    for who, M_, tg in (("ours", T, c["tgt_o"]), ("bambu", B, c["tgt_b"])):
        img, ppm = render(M_, c["az"], c["el"], tg, c["w"], 790, 420)
        img.save(f"{W}/cu2_{nm}_{who}.png")
    print("ok", nm, "px/mm", round(ppm, 4))
