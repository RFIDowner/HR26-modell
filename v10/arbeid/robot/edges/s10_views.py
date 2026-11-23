import sys, math
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from PIL import Image, ImageDraw
from lib import *
T = np.load(OUT + "/ours_full.npy"); B = np.load(OUT + "/bambu_full_nostretch.npy")
B = B[B[:, :, 2].max(1) < 2600]   # drop mast top/sail higher up
W = OUT + "/work"
# side view (from starboard, +y side looking toward -y): u = x (bow left), v = z
Ms = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], float)
# top view: u = x, v = -y? view from above: u = x, v = y, depth = z
Mt = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], float)
for nm, Tm in (("ours", T), ("bambu", B)):
    img, sc = shade_view(Tm, Ms, 1600, box=(-200, 8300, 600, 2000), light=(0.3, 0.8, 0.5))
    # grid ticks every 500 mm
    dr = ImageDraw.Draw(img)
    for gx in range(0, 8300, 500):
        X = (gx + 200) * sc; dr.line([(X, 0), (X, 12)], fill=(255, 0, 0)); dr.text((X + 2, 0), str(gx), fill=(255, 0, 0))
    for gz in range(700, 2000, 100):
        Y = img.height - (gz - 600) * sc; dr.line([(0, Y), (10, Y)], fill=(255, 0, 0)); dr.text((12, Y - 6), str(gz), fill=(255, 0, 0))
    img.save(f"{W}/side_{nm}.png")
    img, sc = shade_view(Tm[Tm[:, :, 1].mean(1) > -50], Mt, 1600, box=(-200, 8300, -100, 1500), light=(0.3, 0.4, 0.85))
    dr = ImageDraw.Draw(img)
    for gx in range(0, 8300, 500):
        X = (gx + 200) * sc; dr.line([(X, 0), (X, 12)], fill=(255, 0, 0)); dr.text((X + 2, 0), str(gx), fill=(255, 0, 0))
    img.save(f"{W}/top_{nm}.png")
print("ok")
