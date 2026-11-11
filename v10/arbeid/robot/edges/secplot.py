import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from PIL import Image, ImageDraw
from lib import *

def plot_sections(items, box, W=900, grid=100.0, title="", fn=None):
    """items: list of (segs (M,2,2) in (u,v), colour, width). box=(umin,umax,vmin,vmax) full-scale mm."""
    umin, umax, vmin, vmax = box
    sc = W / (umax - umin)
    H = int((vmax - vmin) * sc)
    img = Image.new("RGB", (W, H + 30), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    g = np.ceil(umin / grid) * grid
    while g <= umax:
        X = (g - umin) * sc; dr.line([(X, 30), (X, H + 30)], fill=(228, 228, 228)); g += grid
    g = np.ceil(vmin / grid) * grid
    while g <= vmax:
        Y = 30 + H - (g - vmin) * sc; dr.line([(0, Y), (W, Y)], fill=(228, 228, 228)); g += grid
    for segs, col, w in items:
        if segs is None or len(segs) == 0: continue
        for a, b in segs:
            dr.line([((a[0] - umin) * sc, 30 + H - (a[1] - vmin) * sc), ((b[0] - umin) * sc, 30 + H - (b[1] - vmin) * sc)], fill=col, width=w)
    dr.text((6, 6), title + f"   grid {grid:.0f} mm full scale = {grid/30:.2f} mm model", fill=(0, 0, 0), font=font(16))
    if fn: img.save(fn)
    return img
