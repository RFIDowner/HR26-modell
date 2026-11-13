"""Rettet stripe av skrogsiden: bildet samplet i et (x, z)-rutenett paa
skrogsiden (y = side_y(x, z) under dekkskanten, dekkskantens bredde over),
med et loest kamera. Linjer med fast hoeyde blir vannrette, og bilder med
ulike kameraer kan sammenlignes i samme ramme.

Ut: <ut>.npz (x, z, RGB) og <ut>.png (z oppover) med
modellens dekkskant (roed), listens senter (oransje) og vinduet (magenta).

  python ../../../../tools/memcap.py --gb 3 -- python kd_rect.py n4|9387|9374|n6 [x0 x1 dx z0 z1 dz] [ut.png]
"""
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

import common as c
import kd_lib as L
import kd_render as KR
import kd_ovl as O

C, P = L.C, L.P


def side_pts(xs, zs, side):
    X = np.zeros((len(zs), len(xs), 3))
    for j, x in enumerate(xs):
        zsh = C.sheer_z(x)
        hb = C.deck_half_breadth(x)
        for i, z in enumerate(zs):
            if z < zsh - 3.0:
                y = L.G.side_y(x, z)
                if not np.isfinite(y):
                    y = np.nan
            else:
                y = hb
            X[i, j] = (x, side * y, z)
    return X


def rectify(name, xs, zs):
    cam, W, H = KR.cam_named(name)
    side = O.SIDE[name]
    X = side_pts(xs, zs, side)
    ok = np.isfinite(X[..., 1])
    Xf = np.where(ok[..., None], X, 0.0).reshape(-1, 3)
    u, v, d = cam.project(Xf)
    u = u.reshape(ok.shape)
    v = v.reshape(ok.shape)
    im = np.asarray(Image.open(O.IMGS[name]).convert("RGB"), float)
    out = np.zeros(ok.shape + (3,))
    for k in range(3):
        out[..., k] = map_coordinates(im[..., k], [v - 0.5, u - 0.5], order=1, mode="constant", cval=0.0)
    out[~ok] = 0.0
    return out, u, v


def to_png(R, xs, zs, out, scale=(1, 1)):
    img = np.clip(R, 0, 255).astype(np.uint8)[::-1]          # z oppover
    im = Image.fromarray(img)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(im)
    nz = len(zs)

    def row(z):
        return nz - 1 - (z - zs[0]) / (zs[1] - zs[0])

    def col(x):
        return (x - xs[0]) / (xs[1] - xs[0])
    for f, colr in ((C.sheer_z, (255, 40, 40)), (C.strake_z, (255, 140, 0))):
        pts = [(col(x), row(f(x))) for x in xs]
        for i in range(0, len(pts) - 1, 3):
            dr.line(pts[i:i + 2], fill=colr)
    for x in (P.WIN_X0, P.WIN_X1, P.COACH_X1, P.COCKPIT_X0):
        dr.line([(col(x), 0), (col(x), 6)], fill=(255, 0, 255))
    im = im.resize((int(im.width * scale[0]), int(im.height * scale[1])), Image.LANCZOS)
    im.save(out)
    print("skrev", out, im.size)


if __name__ == "__main__":
    a = sys.argv[1:]
    name = a[0]
    if len(a) >= 7:
        x0, x1, dx, z0, z1, dz = (float(v) for v in a[1:7])
    else:
        x0, x1, dx, z0, z1, dz = 2500.0, 7900.0, 10.0, 600.0, 1450.0, 5.0
    xs = np.arange(x0, x1 + 0.1, dx)
    zs = np.arange(z0, z1 + 0.1, dz)
    R, u, v = rectify(name, xs, zs)
    out = a[7] if len(a) >= 8 else c.W + "/out/kd_rect_%s.png" % name
    np.savez_compressed(out[:-4] + ".npz", x=xs, z=zs, rgb=R.astype(np.float32), u=u, v=v)
    to_png(R, xs, zs, out)
