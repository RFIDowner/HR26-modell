"""Enkel STL-renderer for kontrollbilder (ingen eksterne 3D-biblioteker)."""
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw


def load(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    rec = np.frombuffer(
        d,
        dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]),
        count=n,
        offset=84,
    )
    return rec["v"].astype(np.float64), rec["n"].astype(np.float64)


def render(path, out, view="side", W=1400, bg=(255, 255, 255)):
    T, N = load(path)
    R = {
        "side": (0, 2, 1),      # x vannrett, z loddrett, dybde y
        "top": (0, 1, 2),
        "front": (1, 2, 0),
    }[view]
    if view == "iso":
        pass
    u, v, dax = R
    U, V, D = T[:, :, u], T[:, :, v], T[:, :, dax].mean(1)
    if view == "side":
        V = V  # z opp
    umin, umax, vmin, vmax = U.min(), U.max(), V.min(), V.max()
    sc = (W - 40) / max(umax - umin, 1e-9)
    H = int((vmax - vmin) * sc) + 40
    img = Image.new("RGB", (W, max(H, 40)), bg)
    dr = ImageDraw.Draw(img)
    nl = np.array([0.35, 0.45, 0.82])
    nl /= np.linalg.norm(nl)
    nn = N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-9)
    sh = np.clip(np.abs(nn @ nl), 0, 1) * 0.72 + 0.22
    order = np.argsort(D) if view in ("top",) else np.argsort(-D)
    for i in order:
        p = [((U[i, k] - umin) * sc + 20, H - 20 - (V[i, k] - vmin) * sc) for k in range(3)]
        g = int(255 * sh[i])
        dr.polygon(p, fill=(g, g, min(255, g + 14)))
    img.save(out, quality=88)
    return img.size


def iso(path, out, W=1400, az=35.0, el=-24.0, bg=(255, 255, 255)):
    T, N = load(path)
    a, e = np.radians(az), np.radians(el)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    M = Rx @ Rz
    P = T @ M.T
    NN = N @ M.T
    U, V, D = P[:, :, 0], P[:, :, 2], P[:, :, 1].mean(1)
    umin, umax, vmin, vmax = U.min(), U.max(), V.min(), V.max()
    sc = (W - 40) / max(umax - umin, 1e-9)
    H = int((vmax - vmin) * sc) + 40
    img = Image.new("RGB", (W, max(H, 40)), bg)
    dr = ImageDraw.Draw(img)
    nl = np.array([0.3, -0.75, 0.6])
    nl /= np.linalg.norm(nl)
    nn = NN / (np.linalg.norm(NN, axis=1, keepdims=True) + 1e-9)
    sh = np.clip(np.abs(nn @ nl), 0, 1) * 0.7 + 0.24
    for i in np.argsort(D):
        p = [((U[i, k] - umin) * sc + 20, H - 20 - (V[i, k] - vmin) * sc) for k in range(3)]
        g = int(255 * sh[i])
        dr.polygon(p, fill=(g, g, min(255, g + 14)))
    img.save(out, quality=88)
    return img.size


if __name__ == "__main__":
    src, dst, mode = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "side")
    print(iso(src, dst) if mode == "iso" else render(src, dst, mode))
