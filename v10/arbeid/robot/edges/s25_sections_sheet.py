import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from PIL import Image, ImageDraw
from lib import *
W = OUT + "/work"
S = lambda nm: np.load(f"{W}/seg_{nm}.npy")
PW, PH = 388, 300
WMM = 280.0
sc = PW / WMM
def panel(segs, C, col, title, rtxt, flip_u=False):
    img = Image.new("RGB", (PW, PH), (255, 255, 255)); dr = ImageDraw.Draw(img)
    u0 = C[0] - WMM / 2; v0 = C[1] - (PH / sc) / 2
    # grid 20 mm
    for g in np.arange(np.ceil(u0 / 20) * 20, u0 + WMM, 20):
        X = (g - u0) * sc; dr.line([(X, 0), (X, PH)], fill=(235, 235, 235))
    for g in np.arange(np.ceil(v0 / 20) * 20, v0 + PH / sc, 20):
        Y = PH - (g - v0) * sc; dr.line([(0, Y), (PW, Y)], fill=(235, 235, 235))
    for a, b in segs:
        ua, ub = a[0], b[0]
        if flip_u: ua, ub = 2 * C[0] - ua, 2 * C[0] - ub
        dr.line([((ua - u0) * sc, PH - (a[1] - v0) * sc), ((ub - u0) * sc, PH - (b[1] - v0) * sc)], fill=col, width=3)
    f = font(14); fb = font(15)
    dr.rectangle([0, 0, PW, 20], fill=(255, 255, 255))
    dr.text((5, 2), title, font=fb, fill=(0, 0, 0))
    bb = dr.textbbox((5, PH - 22), rtxt, font=f)
    dr.rectangle([bb[0] - 3, bb[1] - 2, bb[2] + 3, bb[3] + 2], fill=(255, 255, 255))
    dr.text((5, PH - 22), rtxt, font=f, fill=col)
    dr.rectangle([0, 0, PW - 1, PH - 1], outline=(180, 180, 180))
    return img
R, Bc = (200, 0, 0), (0, 60, 220)
pairs = [
 ("Deck edge, x=3200", ("ours_x3200", (1132, 1143), "R = 0 (75 deg corner)"), ("bam_x3200", (944, 1305), "R ~22 mm + toe rail, crown R15")),
 ("Coachroof side/roof, x=3200", ("ours_x3200", (922, 1354), "R ~0-4 mm (92 deg)"), ("bam_x3200", (639, 1473), "R ~23 mm (103 deg)")),
 ("Coachroof front, y=0", ("ours_cl_front", (2200, 1300), "vertical wall, R = 0 (not 45 deg)"), ("bam_cl_front", (1415, 1330), "78 deg front, top R ~25 mm")),
 ("Cockpit coaming top, x=6300", ("ours_x6300", (900, 1110), "both top edges R = 0"), ("bam_x6300", (360, 1320), "inner top R ~26 mm")),
 ("Transom top, y=0", ("ours_stern_cl", (7930, 930), "R = 0 (94 deg)"), ("bam_stern_cl", (7830, 1110), "R ~20 mm (82 deg)")),
 ("Transom/side corner, plan z=600", ("ours_plan_z600", (7810, 640), "R = 0 (30-45 deg kink in 4 mm)"), ("bam_plan_z600", (7690, 500), "Rmin 26-53 mm")),
 ("Rubbing strake, x=3200", ("ours_x3200", (1100, 880), "square bar 95 x 55 mm, R = 0"), ("bam_x3200", (975, 1040), "rounded bead ~56 x 16 mm, R~38")),
]
cols = 2
rows = (len(pairs) + 1) // cols
TOP = 64
out = Image.new("RGB", (cols * (2 * PW + 14) + 10, TOP + rows * (PH + 30) + 10), (255, 255, 255))
dr = ImageDraw.Draw(out)
dr.text((10, 8), "Edge sections, full-scale mm (grid 20 mm = 0.67 mm in 1:30). Red = our 01_skrog.stl, blue = Bambu (x0.3708, no y-stretch)", font=font(17), fill=(0, 0, 0))
dr.text((10, 34), "R from corner-cut distance to the two fitted flank lines. Our edges are all sharp (R = 0); Bambu's are rounded R 20-26 mm = 0.7-0.9 mm model.", font=font(15), fill=(60, 60, 60))
for i, (title, o, b) in enumerate(pairs):
    r, c = divmod(i, cols)
    x0 = 10 + c * (2 * PW + 14); y0 = TOP + r * (PH + 30)
    dr.text((x0, y0 + 4), title, font=font(16), fill=(0, 0, 0))
    out.paste(panel(S(o[0]), o[1], R, "ours", o[2]), (x0, y0 + 26))
    out.paste(panel(S(b[0]), b[1], Bc, "Bambu", b[2]), (x0 + PW + 4, y0 + 26))
# legend in last slot
if len(pairs) % 2 == 1:
    x0 = 10 + (2 * PW + 14); y0 = TOP + (rows - 1) * (PH + 30) + 30
    lines = ["Printability at 1:30 (0.2 mm layers, 0.4 mm nozzle):",
             " R 20-30 mm full = 0.7-1.0 mm model: 3-5 layer steps, visible soft edge",
             " R < 9 mm full (< 0.3 mm model): vanishes in print, screen only",
             " Strake: 55 mm proud = 1.8 mm flat overhang underneath (droops);",
             "   a 45-deg or rounded underside prints clean",
             "Sections: transverse (x=const) seen from aft, outboard right;",
             " centreline (y=0) bow left; plan z=600 seen from above."]
    for k, t in enumerate(lines):
        dr.text((x0, y0 + k * 24), t, font=font(15), fill=(40, 40, 40))
out.save(OUT + "/edges_sections.png")
print(out.size)
