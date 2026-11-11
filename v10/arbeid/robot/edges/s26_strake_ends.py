import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from lib import *
from render2 import render
T = np.load(OUT + "/ours_full.npy"); B = np.load(OUT + "/bambu_full_nostretch.npy")
B = B[B[:, :, 2].min(1) < 2300]
W = OUT + "/work"
img, _ = render(T, -35, 8, (330, 120, 1080), 900, 790, 420); img.save(f"{W}/cu3_strake_bow_ours.png")
img, _ = render(B, -35, 8, (330, 120, 1180), 900, 790, 420); img.save(f"{W}/cu3_strake_bow_bambu.png")
img, _ = render(T, 205, 8, (7800, 640, 820), 900, 790, 420); img.save(f"{W}/cu3_strake_stern_ours.png")
img, _ = render(B, 205, 8, (7700, 600, 1000), 900, 790, 420); img.save(f"{W}/cu3_strake_stern_bambu.png")
print("ok")
