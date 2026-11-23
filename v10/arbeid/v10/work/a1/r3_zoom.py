"""Naerbilder: hekkens kvart (WATERPLANE-knekken) og forfoten (bottom_z-spranget). python -I."""
import os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import load_raw, weld, look, raster, face_normals, corner_normals, shade2, components
from PIL import Image, ImageDraw
S = 30.0
def prep(path):
    V, F = weld(load_raw(path))
    lab = components(len(V), F); ul, cnt = np.unique(lab, return_counts=True); F = F[lab == ul[np.argmax(cnt)]]
    fn, area = face_normals(V, F); k = area > 1e-12; F, fn = F[k], fn[k]
    return V, F, fn, corner_normals(V, F, fn)
t = time.time()
M = {"V9": prep(sys.argv[1]), "V10": prep(sys.argv[2])}
print("prep", f"{time.time()-t:.0f}s", flush=True)
def roi_box(V, R, x0, x1, z0, z1):
    X = V[:, 0] * S; Z = V[:, 2] * S - 1400.0
    sel = (X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)
    P = V[sel] @ R.T
    return P[:, :2].min(0), P[:, :2].max(0)
views = {
    "kvart": (40.0, 8.0, 6300.0, 7950.0, -500.0, 1150.0),    # hekkens kvart fra styrbord akter
    "forfot": (125.0, -6.0, 300.0, 2600.0, -450.0, 1250.0),  # forfoten fra styrbord forut, litt nedenfra
}
W = 790
for vn, (az, el, x0, x1, z0, z1) in views.items():
    R = look(az, el)
    lo, hi = roi_box(M["V9"][0], R, x0, x1, z0, z1)
    cols = []
    for nm in ("V9", "V10"):
        V, F, fn, cn = M[nm]
        rr = raster(V, F, R, W, bbox=(lo, hi))
        col = []
        for mode in ("smooth", "zebra"):
            img = Image.fromarray(shade2(rr, fn, cn, R, mode, stripe_deg=4.0))
            ImageDraw.Draw(img).text((10, 8), f"{nm}  {vn}  {mode}", fill=(20, 20, 20))
            col.append(img)
        cols.append(col)
        print(vn, nm, f"{time.time()-t:.0f}s", flush=True)
    Hh = cols[0][0].size[1]
    out = Image.new("RGB", (2 * W + 10, 2 * Hh + 10), (255, 255, 255))
    for c, col in enumerate(cols):
        for r, im in enumerate(col):
            out.paste(im, (c * (W + 10), r * (Hh + 10)))
    out.save(os.path.join(HERE, f"render_zoom_{vn}.png")); print("lagret", vn, out.size, flush=True)
