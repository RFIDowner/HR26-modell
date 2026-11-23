"""Trinn 9 «magen»: de ferdige skrog-STL-ene foer og etter, i samme vinkler
som mage_vis.py (brukerens skjermbilder, nedenfra fra siden, forfra nedenfra),
med vannlinjer (z 0 til -400) og spant (hver 500 mm) tegnet paa skroget.

  python ../../../../tools/memcap.py --gb 3 -- python mage_stl_vis.py UTMAPPE FOER.stl ETTER.stl [navn1 navn2]
"""
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw

import mage_vis as MV


def boat_frame(path):
    """STL fra platen (dreid om Z, skala 1:30) til baatens ramme: x fra baugen,
    y tvers, z fra DWL, kjolbunn -1 400 (som kd_render.load_parts)."""
    m = trimesh.load(path)
    best = None
    for ang in (45.0, -45.0, 135.0, -135.0):
        a = np.radians(-ang)
        R = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
        V = m.vertices @ R.T
        ext = V.max(0) - V.min(0)
        if best is None or ext[0] > best[1][0]:
            best = (V, ext)
    V = best[0] * 30.0
    xs = V[:, 0]
    lo, hi = xs.min(), xs.max()

    def width_near(x0):
        sel = np.abs(xs - x0) < 0.05 * (hi - lo)
        return np.ptp(V[sel, 1])
    if width_near(lo + 0.05 * (hi - lo)) > width_near(hi - 0.05 * (hi - lo)):
        V[:, 0] *= -1
        V[:, 1] *= -1
    V = V + [4.0 - V[:, 0].min(), -0.5 * (V[:, 1].max() + V[:, 1].min()), -1400.0 - V[:, 2].min()]
    return V, np.asarray(m.faces)


def main():
    out, a, b = sys.argv[1:4]
    names = sys.argv[4:6] if len(sys.argv) >= 6 else ["foer", "etter"]
    os.makedirs(out, exist_ok=True)
    meshes = [boat_frame(a), boat_frame(b)]
    VK = np.zeros((0, 3))
    FK = np.zeros((0, 3), int)
    for view in MV.VIEWS:
        tiles = []
        for (V, F), lab in zip(meshes, names):
            im = MV.render(V, F, VK, FK, view, W=1000, H=700)
            ImageDraw.Draw(im).text((14, 10), lab, fill=(0, 0, 0), font=MV.font(28))
            tiles.append(im)
        sheet = Image.new("RGB", (sum(t.width for t in tiles), tiles[0].height), (255, 255, 255))
        x0 = 0
        for t in tiles:
            sheet.paste(t, (x0, 0))
            x0 += t.width
        p = os.path.join(out, "stl_%s.png" % view)
        sheet.save(p)
        print("skrev", p)


if __name__ == "__main__":
    main()
