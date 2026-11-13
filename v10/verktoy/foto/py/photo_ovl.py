import sys, json; sys.path.insert(0, '.')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import common as c, photos as PH
f = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
CB, CA = (0, 200, 255), (255, 0, 200)
for name, crop, pts in (("9391", (0, 550, 1500, 1350), [(PH.L91, 1), (PH.R91, 1)]), ("9388", (100, 600, 1300, 1150), [(PH.L88, 1), (PH.R88, 1)])):
    im = Image.open(c.FOTO + f"/IMG_{name}.jpg").convert("RGB"); d = ImageDraw.Draw(im)
    for tag, col in (("before", CB), ("after", CA)):
        o = json.load(open(c.W + f"/out/outl_{tag}.json"))[name]
        rows, lo, hi = np.array(o["rows"]), np.array(o["lo"]), np.array(o["hi"])
        m = np.isfinite(lo) & (rows > crop[1]) & (rows < crop[3])
        d.line(list(zip(lo[m], rows[m])), fill=col, width=3); d.line(list(zip(hi[m], rows[m])), fill=col, width=3)
        if tag == "after":
            for k, s in o["secs"].items():
                s = np.array(s)
                if len(s) > 1:
                    d.line([tuple(p) for p in s], fill=(255, 120, 230), width=1)
    for arr, side in pts:
        for v, u in arr:
            d.ellipse([u - 3, v - 3, u + 3, v + 3], outline=(255, 255, 0), width=2)
    if name == "9388":
        for u, v in PH.B88:
            d.ellipse([u - 3, v - 3, u + 3, v + 3], outline=(255, 255, 0), width=2)
    im = im.crop(crop)
    d = ImageDraw.Draw(im)
    lab = {"9391": "IMG_9391 from astern, camera solved from fixed features (rms 1-3.5 px)",
           "9388": "IMG_9388 from ahead, camera re-solved (weak: f 2068 px, cream-line misfit 17 px)"}[name]
    d.rectangle([0, 0, im.size[0], 58], fill=(255, 255, 255))
    d.text((8, 4), lab, fill=(0, 0, 0), font=f)
    d.text((8, 30), "cyan = model before, magenta = proposal (thin: proposal sections 3000-7750 below z 250), yellow = traced outline", fill=(0, 0, 0), font=f)
    if im.size[0] > 1600:
        im = im.resize((1600, int(im.size[1] * 1600 / im.size[0])), Image.LANCZOS)
    im.save(c.W + f"/img/ovl_IMG{name}.png")
print("ok")
