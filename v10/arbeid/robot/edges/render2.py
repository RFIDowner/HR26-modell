import sys, math
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
import numpy as np
from PIL import Image, ImageDraw
from lib import *

def render(T, az, el, target, width_mm, Wpx, Hpx, light=None, base=(232, 232, 240), bg=(255, 255, 255), ss=2):
    """Flat-shaded orthographic close-up (like a slicer view). az/el in degrees, target in full-scale mm,
    width_mm = horizontal field of view. Supersampled ss x for clean edges."""
    M = view_matrix(az, el)
    P = T @ M.T
    tgt = M @ np.asarray(target, float)
    sc = Wpx * ss / width_mm
    u0 = tgt[0] - width_mm / 2; v0 = tgt[1] - (Hpx / Wpx) * width_mm / 2
    U = (P[:, :, 0] - u0) * sc
    V = Hpx * ss - (P[:, :, 1] - v0) * sc
    D = P[:, :, 2].mean(1)
    sel = (U.max(1) >= 0) & (U.min(1) <= Wpx * ss) & (V.max(1) >= 0) & (V.min(1) <= Hpx * ss)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    # face normals oriented towards the viewer (two-sided), headlight + key light
    view = M[2]               # towards viewer
    s = np.sign(n @ view); s[s == 0] = 1; n = n * s[:, None]
    if light is None:
        light = 0.55 * view + 0.45 * np.array([-0.2, 0.5, 0.85])
    l = np.asarray(light, float); l /= np.linalg.norm(l)
    inten = 0.28 + 0.72 * np.clip(n @ l, 0, 1)
    img = Image.new("RGB", (Wpx * ss, Hpx * ss), bg)
    dr = ImageDraw.Draw(img)
    idx = np.nonzero(sel)[0]
    idx = idx[np.argsort(D[idx])]
    for i in idx:
        c = inten[i]
        dr.polygon([(U[i, 0], V[i, 0]), (U[i, 1], V[i, 1]), (U[i, 2], V[i, 2])],
                   fill=(int(base[0] * c), int(base[1] * c), int(base[2] * c)))
    return img.resize((Wpx, Hpx), Image.LANCZOS), sc / ss

def label(img, text, xy=(8, 6), size=18, fill=(20, 20, 20)):
    dr = ImageDraw.Draw(img)
    f = font(size)
    x, y = xy
    bb = dr.textbbox((x, y), text, font=f)
    dr.rectangle([bb[0] - 3, bb[1] - 2, bb[2] + 3, bb[3] + 2], fill=(255, 255, 255))
    dr.text((x, y), text, font=f, fill=fill)
    return img

def scalebar(img, px_per_mm, mm=300, xy=None):
    dr = ImageDraw.Draw(img)
    L = mm * px_per_mm
    x, y = xy if xy else (img.width - L - 16, img.height - 18)
    dr.line([(x, y), (x + L, y)], fill=(0, 0, 0), width=3)
    dr.text((x, y - 18), f"{mm:.0f} mm full = {mm/30:.0f} mm model", font=font(13), fill=(0, 0, 0))
    return img
