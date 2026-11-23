"""Gjengivelser V9 | A1 | A2, flat og glatt skyggelegging, samme kamera.
STL-ene i baatkoordinater (modell-mm, baugspiss x=0, kjol z=0).
argv: v9.stl a1.stl a2.stl tag"""
import os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import load_raw, weld, look, raster, face_normals, corner_normals, shade2, components
from PIL import Image, ImageDraw
S = 30.0
paths = sys.argv[1:4]
tag = sys.argv[4] if len(sys.argv) > 4 else "a2"
NAMES = ["V9", "A1", "A2"]
XB = [4.0, 4.0, 4.0]


def prep(path, xb):
    V, F = weld(load_raw(path))
    V = V.copy()
    V[:, 0] += xb / S                      # samme x som baatens (baugspissen ved xb)
    lab = components(len(V), F)
    ul, cnt = np.unique(lab, return_counts=True)
    F = F[lab == ul[np.argmax(cnt)]]       # bare ytterskallet
    fn, area = face_normals(V, F)
    k = area > 1e-12
    F, fn = F[k], fn[k]
    return V, F, fn, corner_normals(V, F, fn)


t = time.time()
M = [prep(p, xb) for p, xb in zip(paths, XB)]
print("lest", f"{time.time()-t:.0f}s", flush=True)


def roi(V, R, box):
    if box is None:
        P = V @ R.T
        return P[:, :2].min(0), P[:, :2].max(0)
    x0, x1, z0, z1 = box
    X = V[:, 0] * S
    Z = V[:, 2] * S - 1400.0
    sel = (X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)
    P = V[sel] @ R.T
    return P[:, :2].min(0), P[:, :2].max(0)


views = {
    "baug34": (148.0, 14.0, None),
    "hekk34": (35.0, 16.0, None),
    "baug_naer": (135.0, 18.0, (0.0, 2600.0, 300.0, 1320.0)),
    "hekk_naer": (40.0, 10.0, (5600.0, 7950.0, -500.0, 1150.0)),
}
W = 520
for vn, (az, el, box) in views.items():
    R = look(az, el)
    lo, hi = roi(M[0][0], R, box)
    rows = []
    for mode in ("flat", "smooth"):
        row = []
        for nm, (V, F, fn, cn) in zip(NAMES, M):
            rr = raster(V, F, R, W, bbox=(lo, hi))
            img = Image.fromarray(shade2(rr, fn, cn, R, mode, stripe_deg=3.0))
            ImageDraw.Draw(img).text((10, 8), f"{nm}  {vn}  {mode}", fill=(20, 20, 20))
            row.append(img)
        rows.append(row)
    Hh = rows[0][0].size[1]
    out = Image.new("RGB", (3 * W + 20, 2 * Hh + 10), (255, 255, 255))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            out.paste(im, (c * (W + 10), r * (Hh + 10)))
    fn_out = os.path.join(HERE, f"render_{vn}_{tag}.png")
    out.save(fn_out)
    print("lagret", fn_out, out.size, f"{time.time()-t:.0f}s", flush=True)
