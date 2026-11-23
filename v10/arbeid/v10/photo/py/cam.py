"""Camera models (orthographic with anisotropy, pinhole), z-buffer renderer for the baseline mesh."""
import numpy as np


def rot(yaw, pitch, roll):
    """World->camera rotation. Camera looks along +d. yaw about Z (deg), pitch (deg, +up), roll (deg).
    yaw=0: camera looks along -Y (i.e. it stands on +Y side = port side, sees the port topsides), image right = +X? we define
    base frame: right = +X (bow -> stern to the right), up = +Z, forward(view) = -Y."""
    y, p, r = np.radians([yaw, pitch, roll])
    # base: rows = right, up, back(toward viewer)
    B = np.array([[1.0, 0, 0], [0, 0, 1.0], [0, 1.0, 0]])  # right=X, up=Z, back=+Y (viewer on +Y side)
    Rz = np.array([[np.cos(y), -np.sin(y), 0], [np.sin(y), np.cos(y), 0], [0, 0, 1]])
    # pitch: rotate camera about its right axis; roll: about view axis
    Rp = np.array([[1, 0, 0], [0, np.cos(p), -np.sin(p)], [0, np.sin(p), np.cos(p)]])
    Rr = np.array([[np.cos(r), -np.sin(r), 0], [np.sin(r), np.cos(r), 0], [0, 0, 1]])
    return Rr @ Rp @ B @ Rz.T


def generic_rot(fwd, up_hint=(0, 0, 1.0), roll=0.0):
    """rows: right, up, back for a camera looking along fwd (world)."""
    f = np.asarray(fwd, float); f /= np.linalg.norm(f)
    r = np.cross(f, up_hint); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    R = np.stack([r, u, -f])
    c, s = np.cos(np.radians(roll)), np.sin(np.radians(roll))
    Rr = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return Rr @ R


def ortho(P, R, su, sv, u0, v0):
    Q = P @ R.T
    return np.c_[u0 + su * Q[:, 0], v0 - sv * Q[:, 1]], Q[:, 2]


def pinhole(P, R, C, f, cx, cy, asp=1.0):
    """C camera centre (world). Returns uv, depth (positive in front)."""
    Q = (P - C) @ R.T          # right, up, back
    z = -Q[:, 2]
    return np.c_[cx + f * Q[:, 0] / z, cy - f * asp * Q[:, 1] / z], z


def raster_uv(uv, depth, F, W, H):
    """z-buffer: nearest = smallest depth. Returns fid (H,W) and depth buffer."""
    px, py = uv[:, 0], uv[:, 1]
    zb = np.full((H, W), np.inf); fid = np.full((H, W), -1, np.int64)
    X0, X1, X2 = px[F[:, 0]], px[F[:, 1]], px[F[:, 2]]
    Y0, Y1, Y2 = py[F[:, 0]], py[F[:, 1]], py[F[:, 2]]
    Z0, Z1, Z2 = depth[F[:, 0]], depth[F[:, 1]], depth[F[:, 2]]
    ok = (Z0 > 0) & (Z1 > 0) & (Z2 > 0)
    xmin = np.floor(np.minimum(np.minimum(X0, X1), X2)).astype(np.int64)
    xmax = np.ceil(np.maximum(np.maximum(X0, X1), X2)).astype(np.int64)
    ymin = np.floor(np.minimum(np.minimum(Y0, Y1), Y2)).astype(np.int64)
    ymax = np.ceil(np.maximum(np.maximum(Y0, Y1), Y2)).astype(np.int64)
    ok &= (xmax >= 0) & (xmin < W) & (ymax >= 0) & (ymin < H)
    xmin = np.clip(xmin, 0, W - 1); xmax = np.clip(xmax, 0, W - 1); ymin = np.clip(ymin, 0, H - 1); ymax = np.clip(ymax, 0, H - 1)
    den = (Y1 - Y2) * (X0 - X2) + (X2 - X1) * (Y0 - Y2)
    ok &= np.abs(den) > 1e-12
    bw = xmax - xmin + 1; bh = ymax - ymin + 1
    area = bw * bh
    idx_all = np.nonzero(ok)[0]
    edges = (0, 4, 16, 64, 256, 1024, 4096, 16384, 10 ** 12)
    for lo_a, hi_a in zip(edges[:-1], edges[1:]):
        sel = idx_all[(area[idx_all] > lo_a) & (area[idx_all] <= hi_a)]
        if len(sel) == 0:
            continue
        mw = int(bw[sel].max()); mh = int(bh[sel].max())
        chunk = max(1, int(3_000_000 // (mw * mh)))
        for c0 in range(0, len(sel), chunk):
            s = sel[c0:c0 + chunk]
            gx = xmin[s][:, None, None] + np.arange(mw)[None, None, :]
            gy = ymin[s][:, None, None] + np.arange(mh)[None, :, None]
            cx = gx + 0.5; cy = gy + 0.5
            l0 = ((Y1[s] - Y2[s])[:, None, None] * (cx - X2[s][:, None, None]) + (X2[s] - X1[s])[:, None, None] * (cy - Y2[s][:, None, None])) / den[s][:, None, None]
            l1 = ((Y2[s] - Y0[s])[:, None, None] * (cx - X2[s][:, None, None]) + (X0[s] - X2[s])[:, None, None] * (cy - Y2[s][:, None, None])) / den[s][:, None, None]
            l2 = 1 - l0 - l1
            inside = (l0 >= -1e-9) & (l1 >= -1e-9) & (l2 >= -1e-9) & (gx <= xmax[s][:, None, None]) & (gy <= ymax[s][:, None, None])
            zz = l0 * Z0[s][:, None, None] + l1 * Z1[s][:, None, None] + l2 * Z2[s][:, None, None]
            ti, yy, xx = np.nonzero(inside)
            if len(ti) == 0:
                continue
            gxx = gx[ti, 0, xx]; gyy = gy[ti, yy, 0]
            z = zz[ti, yy, xx]
            pix = gyy * W + gxx
            o = np.lexsort((z, pix))
            pix_o = pix[o]
            first = np.r_[True, pix_o[1:] != pix_o[:-1]]
            o = o[first]
            pix_s = pix[o]; z_s = z[o]
            cur = zb.ravel()[pix_s]
            win = z_s < cur
            o = o[win]; pix_s = pix_s[win]
            zb.ravel()[pix_s] = z[o]
            fid.ravel()[pix_s] = s[ti[o]]
    return fid, zb


def shade(fid, fn, R, light=(-0.3, 0.6, 0.75)):
    m = fid >= 0
    n = fn[fid[m]] @ R.T
    flip = n[:, 2] < 0
    n[flip] *= -1
    L = np.array(light, float); L /= np.linalg.norm(L)
    d = np.clip(n @ L, 0, 1)
    img = np.zeros(fid.shape)
    img[m] = 0.25 + 0.75 * d
    return img


def face_normals(V, F):
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    a = np.linalg.norm(n, axis=1)
    return n / np.maximum(a, 1e-30)[:, None]
