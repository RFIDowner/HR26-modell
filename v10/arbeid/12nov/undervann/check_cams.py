"""Overlay today's hull (int4 STL silhouette, cyan) and the analytic hull (magenta) on the photos with the PHOTO_VIEWS cameras."""
import sys, time, json
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/undervann/py")
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import uw

t = time.time()
Vs, Fs = uw.load_int4()
print("stl", Vs.shape, Fs.shape, "x %.0f..%.0f z %.0f..%.0f" % (Vs[:, 0].min(), Vs[:, 0].max(), Vs[:, 2].min(), Vs[:, 2].max()), time.time() - t)
t = time.time()
Va, Fa = uw.hull_mesh()
print("analytic", Va.shape, Fa.shape, time.time() - t)
for name in ("IMG_9388", "IMG_9391", "IMG_9389"):
    cam = uw.cam_from(uw.cam_params0(name), name)
    img = uw.photo(name).copy()
    t = time.time()
    fid, _ = uw.S.raster(cam, Vs, Fs, cull=False)
    m = fid >= 0
    edge = m & ~ndi.binary_erosion(m)
    edge = ndi.binary_dilation(edge, iterations=1)
    img[edge] = (0, 230, 255)
    print(name, "raster", time.time() - t)
    t = time.time()
    if name == "IMG_9389":
        rows = np.arange(0, cam.W, 2.0)
        lo, hi, _, _ = uw.row_extents(cam, Va, Fa, rows, axis="col")
        pts = [(r, h) for r, h in zip(rows, hi) if np.isfinite(h)] + [(r, l) for r, l in zip(rows, lo) if np.isfinite(l)]
    else:
        rows = np.arange(0, cam.H, 2.0)
        lo, hi, _, _ = uw.row_extents(cam, Va, Fa, rows)
        pts = [(l, r) for r, l in zip(rows, lo) if np.isfinite(l)] + [(h, r) for r, h in zip(rows, hi) if np.isfinite(h)]
    print(name, "extents", time.time() - t)
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    for p in pts:
        d.point(p, fill=(255, 0, 255))
    im.save(uw.OUT + f"/view/cam0_{name}.png")
