"""Lower edge of the black (antifouling) region in the brochure 1:50 profile crop, per column.
bcal (kjol): x=(2536.2-px)*3.28, z=(598.6-py)*3.28."""
import sys; sys.path.insert(0, '.')
import numpy as np
from PIL import Image
import common as c
from prof_cmp import u_z
im = np.asarray(Image.open(c.OLD + "/enderlein/work/broch_p6_prof.png").convert("L"), float)
H, Wd = im.shape
def x_of(px): return (2536.2 - px) * 3.28
def z_of(py): return (598.6 - py) * 3.28
out = []
for px in range(150, 1890, 2):
    col = im[:, px]
    # search downward from row 610 for the last dark pixel of the first dark run reaching below 700
    dark = col < 110
    rows = np.where(dark[600:])[0] + 600
    if len(rows) == 0:
        continue
    # contiguous run starting from the first dark row after 600
    r0 = rows[0]; r = r0
    while r + 1 < H and dark[r + 1]:
        r += 1
    # subpixel: threshold crossing between r and r+1 at level mid of dark/light
    v0, v1 = col[r], col[min(r + 1, H - 1)]
    lvl = 0.5 * (col[max(r - 3, 0)] + col[min(r + 4, H - 1)])
    f = (lvl - v0) / (v1 - v0) if v1 != v0 else 0.5
    yb = r + np.clip(f, 0, 1)
    out.append((x_of(px), z_of(yb + 0.5), r0))
out = np.array(out)
c.save_json(out, c.W + "/out/btrace_aft.json")
for x in [2200, 2400, 2600, 2800, 3000, 5800, 5900, 6000, 6500, 6600, 6800, 7000, 7100, 7200, 7300, 7400, 7500, 7600, 7650, 7700]:
    m = np.abs(out[:, 0] - x) < 5
    if m.any():
        print(f"x {x}: brochure-trace z {out[m,1].mean():7.1f}  uw_station {u_z(x):7.1f}")
