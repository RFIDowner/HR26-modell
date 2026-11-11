"""Naerbilder av STL-er i fullskala baatkoordinater (x fra baugen, z over DWL).

python rend.py out.png W az el roi(x0,x1,y0,y1,z0,z1) file1[:kind] file2[:kind] ...
kind = full (allerede fullskala, default) | model (build_hull_only-STL: x*30+4, y*30, z*30-1400)
Glatt skygge med kantbevarende normaler (crease 30 grader).
"""
import sys, time
import numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/c")
from common import load_raw, weld, face_normals, corner_normals, look, raster, shade2
from PIL import Image, ImageDraw


def load(spec):
    path, kind = spec, "full"
    if spec.endswith(":model") or spec.endswith(":full"):
        path, _, kind = spec.rpartition(":")
    T = load_raw(path).astype(np.float64)
    if kind == "model":
        T = T * 30.0
        T[:, :, 0] += 4.0
        T[:, :, 2] -= 1400.0
    return T


def render(out, W, az, el, roi, specs, label=None, crease=30.0, mode="smooth"):
    x0, x1, y0, y1, z0, z1 = roi
    tris = []
    for s in specs:
        T = load(s)
        c = T.mean(axis=1)
        m = (c[:, 0] > x0) & (c[:, 0] < x1) & (c[:, 1] > y0) & (c[:, 1] < y1) & (c[:, 2] > z0) & (c[:, 2] < z1)
        tris.append(T[m])
    T = np.concatenate(tris).astype(np.float32)
    V, F = weld(T)
    fn, area = face_normals(V, F)
    ok = area > 1e-9
    F, fn = F[ok], fn[ok]
    cn = corner_normals(V, F, fn, crease_deg=crease)
    R = look(az, el)
    corners = np.array([[a, b, c] for a in (x0, x1) for b in (y0, y1) for c in (z0, z1)], float)
    P = corners @ R.T
    bbox = (P[:, :2].min(0), P[:, :2].max(0))
    t = time.time()
    rr = raster(V, F, R, W, bbox=bbox)
    img = Image.fromarray(shade2(rr, fn, cn, R, mode))
    if label:
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 9 * len(label) + 12, 20], fill=(255, 255, 255))
        d.text((6, 4), label, fill=(0, 0, 0))
    img.save(out)
    print(out, img.size, f"{len(F)} tri, {time.time() - t:.1f}s")
    return img


if __name__ == "__main__":
    out, W, az, el = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    roi = [float(v) for v in sys.argv[5].split(",")]
    render(out, W, az, el, roi, sys.argv[6:])
