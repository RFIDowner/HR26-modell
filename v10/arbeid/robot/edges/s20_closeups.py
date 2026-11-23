import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from PIL import Image, ImageDraw
from lib import *
from render2 import render, label, scalebar
T = np.load(OUT + "/ours_full.npy"); B = np.load(OUT + "/bambu_full_nostretch.npy")
B = B[B[:, :, 2].min(1) < 2300]
W = OUT + "/work"
cells = {
  "bow":     dict(az=-38, el=22, tgt_o=(450, 0, 1050), tgt_b=(450, 0, 1150), w=1700),
  "stern":   dict(az=212, el=24, tgt_o=(7450, 300, 1000), tgt_b=(7350, 250, 1150), w=2300),
  "deck":    dict(az=-62, el=28, tgt_o=(3300, 900, 1150), tgt_b=(3300, 750, 1300), w=2300),
  "front":   dict(az=-28, el=26, tgt_o=(2350, 250, 1260), tgt_b=(1550, 250, 1330), w=1500),
}
for nm, c in cells.items():
    for who, M_, tg in (("ours", T, c["tgt_o"]), ("bambu", B, c["tgt_b"])):
        img, ppm = render(M_, c["az"], c["el"], tg, c["w"], 790, 470)
        img.save(f"{W}/cu_{nm}_{who}.png")
    print("ok", nm)
