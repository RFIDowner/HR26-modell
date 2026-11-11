import sys, time; sys.path.insert(0, "..")
import numpy as np, score as S
from PIL import Image
for tag in ["fine", "skrog"]:
    V = np.load(f"V_{tag}.npy"); F = np.load(f"F_{tag}.npy")
    fn, *_ = S.face_geom(V, F)
    W, H = 520, 300
    tiles = []
    t0 = time.time()
    for spec in S.FIXED_VIEWS:
        t = time.time()
        cam = S.view_cam(spec, V, W, H)
        im, mask = S.render_view(cam, V, F, fn, ss=2)
        tiles.append(im)
        print(tag, spec[0], "%.1fs" % (time.time() - t), "coverage", mask.mean().round(3))
    sheet = Image.new("RGB", (3 * W, 2 * H), (255, 255, 255))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % 3) * W, (i // 3) * H))
    sheet.save(f"views_{tag}.png")
    print(tag, "total %.1fs" % (time.time() - t0))
