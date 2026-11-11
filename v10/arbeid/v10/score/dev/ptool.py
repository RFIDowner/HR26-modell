"""Photo camera fit: landmarks -> perspective camera; overlay of the model silhouette."""
import sys, json, math
sys.path.insert(0, "..")
import numpy as np, score as S
from PIL import Image, ImageOps, ImageDraw
from scipy.optimize import least_squares

V = np.load("V_fine.npy"); F = np.load("F_fine.npy")
fn, *_ = S.face_geom(V, F)

def photo(name):
    return ImageOps.exif_transpose(Image.open(f"C:/Users/stig/Documents/Seilbåt/{name}.jpeg")).convert("RGB")

def cam_from(p, W, H):
    # p = (cx_world, cy_world, cz_world, yaw, pitch, roll, f)
    C = np.array(p[:3]); R = S.rot_from_euler(p[3], p[4], p[5])
    return S.Cam(C, R, W, H, f=p[6], cx=W / 2.0, cy=H / 2.0)

def solve(lm, W, H, p0, fix_f=None, weights=None):
    X = np.array([a for a, b in lm], float); x = np.array([b for a, b in lm], float)
    w = np.ones(len(lm)) if weights is None else np.asarray(weights, float)
    def res(p):
        q = list(p)
        if fix_f is not None:
            q = q + [fix_f]
        c = cam_from(q, W, H)
        u, v, z = c.project(X)
        return (np.r_[u - x[:, 0], v - x[:, 1]]) * np.r_[w, w]
    p0 = list(p0) if fix_f is None else list(p0[:6])
    r = least_squares(res, p0, x_scale="jac")
    q = list(r.x) + ([fix_f] if fix_f is not None else [])
    c = cam_from(q, W, H)
    u, v, _ = c.project(X)
    err = np.hypot(u - x[:, 0], v - x[:, 1])
    return q, err

def overlay(name, p, out, crop=None, lm=None, scale=0.5):
    im = photo(name)
    W, H = im.size
    c = cam_from(p, W, H)
    cs = c.scaled(scale)
    fid, _ = S.raster(cs, V, F)
    m = fid >= 0
    edge = m ^ np.pad(m, 1, mode="edge")[1:-1, 2:] | m ^ np.pad(m, 1, mode="edge")[2:, 1:-1]
    sm = im.resize((cs.W, cs.H), Image.LANCZOS)
    a = np.asarray(sm).copy()
    a[edge] = (0, 255, 255)
    ov = Image.fromarray(a)
    d = ImageDraw.Draw(ov)
    if lm:
        X = np.array([q for q, _ in lm]); u, v, _ = cs.project(X)
        for (q, (px, py)), uu, vv in zip(lm, u, v):
            d.ellipse([px * scale - 4, py * scale - 4, px * scale + 4, py * scale + 4], outline=(255, 0, 0), width=2)
            d.line([px * scale, py * scale, uu, vv], fill=(255, 255, 0), width=2)
    if crop:
        ov = ov.crop([int(v * scale) for v in crop])
    ov.save(out)
    return ov.size
