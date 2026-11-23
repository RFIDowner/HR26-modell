"""Hele modellen (export/stl/01_skrog.stl) i baatens ramme, rendret med et
IMG_9389-kamera (score.py: load_stl, weld, detect_frame, to_build_frame,
raster, shade). Bruk:
  python stl9389.py <kamera.json|-> <ut.png> [skala]
Lagrer ogsaa en maske (ut_mask.npy) med flate-id per piksel ved skala."""
import json
import os
import sys

import numpy as np

import common as c

sys.path.insert(0, os.path.join(c.REPO, "v10", "arbeid", "v10", "score"))
import score as S  # noqa: E402

STL = os.path.join(c.REPO, "export", "stl", "01_skrog.stl")
import tempfile  # noqa: E402
_CACHE = os.path.join(tempfile.gettempdir(), "hr26_stl9389_cache.npz")


def model_mesh():
    """V (mm, baatens ramme), F. Mellomlagret i %TEMP%/hr26_stl9389_cache.npz."""
    if os.path.exists(_CACHE) and os.path.getmtime(_CACHE) > os.path.getmtime(STL):
        d = np.load(_CACHE)
        return d["V"], d["F"]
    T, _ = S.load_stl(STL)
    Vm, F = S.weld(T, 1e-5)
    if S.signed_volume(Vm, F).sum() < 0:
        F = F[:, ::-1].copy()
    fr = S.detect_frame(Vm, "auto")
    V = S.to_build_frame(Vm, fr, 4.0)
    np.savez_compressed(_CACHE, V=V.astype(np.float32), F=F.astype(np.int32))
    return V, F


def render(p, k=0.5, V=None, F=None):
    """Rendrer modellen med uwlib-kameraet p (2000 x 1500) skalert k."""
    if V is None:
        V, F = model_mesh()
    V = np.asarray(V, float)
    R = S.rot_from_euler(p[3], p[4], p[5])
    cam = S.Cam(p[:3], R, round(2000 * k), round(1500 * k), f=p[6] * k)
    fid, depth = S.raster(cam, V, F)
    fn, _, _, _, _ = S.face_geom(V, F)
    img = S.shade(cam, fid, fn)
    return img, fid, depth, cam


if __name__ == "__main__":
    from PIL import Image
    if sys.argv[1] == "-":
        p = json.load(open(c.W + "/out/cam9389.json"))["p"]
    else:
        j = json.load(open(sys.argv[1]))
        p = j["p"] if isinstance(j, dict) else j
    k = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    img, fid, depth, cam = render(p, k)
    Image.fromarray(img).save(sys.argv[2])
    np.save(sys.argv[2][:-4] + "_mask.npy", fid >= 0)
