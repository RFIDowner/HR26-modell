"""Trinn 9: omrisset foer (blaa) og etter (roed) tegnet paa etter-bildet, fra
bildene mage_stl_vis.py lager (to fliser side om side, hvit bakgrunn).

  python mage_kontur.py INNMAPPE UTMAPPE
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import mage_vis as MV


def outline(mask):
    er = ndimage.binary_erosion(mask, iterations=2)
    return mask & ~er


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for view in MV.VIEWS:
        p = os.path.join(src, "stl_%s.png" % view)
        if not os.path.exists(p):
            continue
        im = np.asarray(Image.open(p).convert("RGB")).astype(int)
        w = im.shape[1] // 2
        a, b = im[:, :w], im[:, w:2 * w]
        ma = (np.abs(a - 255).sum(2) > 30)
        mb = (np.abs(b - 255).sum(2) > 30)
        ma[:60] = False
        mb[:60] = False
        ma = ndimage.binary_fill_holes(ndimage.binary_closing(ma, iterations=2))
        mb = ndimage.binary_fill_holes(ndimage.binary_closing(mb, iterations=2))
        res = (0.55 * b + 0.45 * 255).astype(np.uint8)
        oa, ob = outline(ma), outline(mb)
        res[ob] = (220, 0, 40)
        res[oa] = (0, 80, 230)
        img = Image.fromarray(res)
        d = ImageDraw.Draw(img)
        d.text((14, 10), "omriss foer trinn 9 (blaa) og etter (roed)", fill=(0, 0, 0), font=MV.font(26))
        img.save(os.path.join(out, "kontur_%s.png" % view))
        print("skrev", os.path.join(out, "kontur_%s.png" % view), "piksler ny utenfor gammel: %d, gammel utenfor ny: %d"
              % ((mb & ~ma).sum(), (ma & ~mb).sum()))


if __name__ == "__main__":
    main()
