"""Shared helpers: STL loading, welding, adjacency, classification, rasterizer."""
import math, struct, sys
import numpy as np

REPO = r"C:/Users/stig/Documents/GitHub/HR26-modell"
OURS = REPO + "/export/stl/01_skrog.stl"
BAMBU = r"C:/Users/stig/Downloads/Seilbåt fra Bambumotor.stl"
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b"
S = 30.0


def load_raw(path):
    d = open(path, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    rec = np.frombuffer(d, dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("a", "<u2")]), count=n, offset=84)
    return rec["v"].copy()          # float32 (n,3,3)


def weld(T32, q=None):
    """Exact weld on float32 bits (q=None) or quantized weld (q in mm)."""
    V = T32.reshape(-1, 3)
    if q is None:
        key = np.ascontiguousarray(V).view(np.dtype((np.void, 12))).ravel()
    else:
        key = np.round(V.astype(np.float64) / q).astype(np.int64)
        key = np.ascontiguousarray(key).view(np.dtype((np.void, 24))).ravel()
    _, first, inv = np.unique(key, return_index=True, return_inverse=True)
    verts = V[first].astype(np.float64)
    F = inv.reshape(-1, 3)
    return verts, F


def rotz(P, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return P @ R.T


def edges_adjacency(F):
    """Returns unique edges (E,2), and for manifold edges the two faces."""
    nf = len(F)
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    fid = np.concatenate([np.arange(nf)] * 3)
    es = np.sort(e, axis=1)
    key = es[:, 0].astype(np.int64) * (F.max() + 1) + es[:, 1]
    order = np.argsort(key, kind="stable")
    ks = key[order]
    uniq, start, counts = np.unique(ks, return_index=True, return_counts=True)
    man = counts == 2
    f1 = fid[order[start[man]]]
    f2 = fid[order[start[man] + 1]]
    E = es[order[start[man]]]
    return E, f1, f2, counts


def face_normals(V, F):
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    a = np.linalg.norm(n, axis=1)
    return n / np.maximum(a, 1e-30)[:, None], 0.5 * a


def components(nv, F):
    """Connected components over faces sharing vertices -> label per face."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    a = np.concatenate([F[:, 0], F[:, 1], F[:, 2]])
    b = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
    g = coo_matrix((np.ones(len(a)), (a, b)), shape=(nv, nv))
    _, lab = connected_components(g, directed=False)
    return lab[F[:, 0]]


def to_full(V, xbow_model, xbow_full=4.0):
    """model (rotated, bow at min x) -> full-scale (x from bow, y, z over DWL)."""
    X = (V[:, 0] - xbow_model) * S + xbow_full
    Y = V[:, 1] * S
    Z = V[:, 2] * S - 1400.0
    return np.c_[X, Y, Z]


# ------------------------------------------------------------------ renderer
def look(az_deg, el_deg):
    """Camera rotation: returns R so that P_cam = P @ R.T ; cam x right, y up, z toward viewer."""
    a, e = math.radians(az_deg), math.radians(el_deg)
    # view direction from camera to target
    d = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    fwd = -d  # camera looks along -d? we define d as direction from target to camera
    zc = d / np.linalg.norm(d)
    up = np.array([0, 0, 1.0])
    xc = np.cross(up, zc); xc /= np.linalg.norm(xc)
    yc = np.cross(zc, xc)
    return np.stack([xc, yc, zc])


def raster(V, F, R, W, H=None, pad=12, vnormals=None, bbox=None):
    """Orthographic z-buffer. Returns depth, face id, barycentrics (per pixel) and the 2D transform.
    Pure numpy, triangle-by-bounding-box vectorized in chunks."""
    P = V @ R.T
    if bbox is None:
        used = np.unique(F)
        lo = P[used, :2].min(0); hi = P[used, :2].max(0)
    else:
        lo, hi = bbox
    sc = (W - 2 * pad) / (hi[0] - lo[0])
    if H is None:
        H = int((hi[1] - lo[1]) * sc) + 2 * pad
    px = (P[:, 0] - lo[0]) * sc + pad
    py = H - pad - (P[:, 1] - lo[1]) * sc
    pz = P[:, 2]
    depth = np.full((H, W), -np.inf)
    fid = np.full((H, W), -1, np.int64)
    b0 = np.zeros((H, W)); b1 = np.zeros((H, W))
    X0, X1, X2 = px[F[:, 0]], px[F[:, 1]], px[F[:, 2]]
    Y0, Y1, Y2 = py[F[:, 0]], py[F[:, 1]], py[F[:, 2]]
    Z0, Z1, Z2 = pz[F[:, 0]], pz[F[:, 1]], pz[F[:, 2]]
    xmin = np.clip(np.floor(np.minimum(np.minimum(X0, X1), X2)).astype(int), 0, W - 1)
    xmax = np.clip(np.ceil(np.maximum(np.maximum(X0, X1), X2)).astype(int), 0, W - 1)
    ymin = np.clip(np.floor(np.minimum(np.minimum(Y0, Y1), Y2)).astype(int), 0, H - 1)
    ymax = np.clip(np.ceil(np.maximum(np.maximum(Y0, Y1), Y2)).astype(int), 0, H - 1)
    den = (Y1 - Y2) * (X0 - X2) + (X2 - X1) * (Y0 - Y2)
    ok = np.abs(den) > 1e-12
    bw = xmax - xmin + 1; bh = ymax - ymin + 1
    # group triangles by bbox size to vectorize
    area = bw * bh
    idx_all = np.nonzero(ok)[0]
    for lo_a, hi_a in ((0, 16), (16, 64), (64, 256), (256, 1024), (1024, 4096), (4096, 10 ** 9)):
        sel = idx_all[(area[idx_all] > lo_a) & (area[idx_all] <= hi_a)] if lo_a else idx_all[area[idx_all] <= hi_a]
        if len(sel) == 0:
            continue
        mw = int(bw[sel].max()); mh = int(bh[sel].max())
        chunk = max(1, int(4_000_000 // (mw * mh)))
        for c0 in range(0, len(sel), chunk):
            s = sel[c0:c0 + chunk]
            gx = xmin[s][:, None, None] + np.arange(mw)[None, None, :]
            gy = ymin[s][:, None, None] + np.arange(mh)[None, :, None]
            cx = gx + 0.5; cy = gy + 0.5
            l0 = ((Y1[s] - Y2[s])[:, None, None] * (cx - X2[s][:, None, None]) + (X2[s] - X1[s])[:, None, None] * (cy - Y2[s][:, None, None])) / den[s][:, None, None]
            l1 = ((Y2[s] - Y0[s])[:, None, None] * (cx - X2[s][:, None, None]) + (X0[s] - X2[s])[:, None, None] * (cy - Y2[s][:, None, None])) / den[s][:, None, None]
            l2 = 1 - l0 - l1
            inside = (l0 >= -1e-9) & (l1 >= -1e-9) & (l2 >= -1e-9) & (gx <= xmax[s][:, None, None]) & (gy <= ymax[s][:, None, None]) & (gx < W) & (gy < H)
            zz = l0 * Z0[s][:, None, None] + l1 * Z1[s][:, None, None] + l2 * Z2[s][:, None, None]
            ti, yy, xx = np.nonzero(inside)
            if len(ti) == 0:
                continue
            gxx = gx[ti, 0, xx]; gyy = gy[ti, yy, 0]
            z = zz[ti, yy, xx]
            # resolve: keep max z per pixel (nearest to viewer, cam z toward viewer)
            pix = gyy * W + gxx
            o = np.lexsort((z, pix))
            pix_o = pix[o]
            last = np.r_[pix_o[1:] != pix_o[:-1], True]
            o = o[last]
            pix_s = pix[o]; z_s = z[o]
            cur = depth.ravel()[pix_s]
            win = z_s > cur
            o = o[win]; pix_s = pix_s[win]
            depth.ravel()[pix_s] = z[o]
            fid.ravel()[pix_s] = s[ti[o]]
            b0.ravel()[pix_s] = l0[ti[o], yy[o], xx[o]]
            b1.ravel()[pix_s] = l1[ti[o], yy[o], xx[o]]
    return dict(depth=depth, fid=fid, b0=b0, b1=b1, H=H, W=W, sc=sc, lo=lo, pad=pad)


def vertex_normals(V, F, fn, area, crease_deg=None):
    """Area-weighted vertex normals (no crease splitting)."""
    vn = np.zeros_like(V)
    w = (fn * area[:, None])
    for k in range(3):
        np.add.at(vn, F[:, k], w)
    vn /= np.maximum(np.linalg.norm(vn, axis=1), 1e-30)[:, None]
    return vn


def shade(rr, V, F, fn, R, mode="flat", vn=None, light=(0.35, 0.55, 0.75), zebra_period=None, base=(205, 208, 222)):
    fid = rr["fid"]; m = fid >= 0
    f = fid[m]
    if mode == "flat":
        n = fn[f]
    else:
        l0 = rr["b0"][m]; l1 = rr["b1"][m]; l2 = 1 - l0 - l1
        n = l0[:, None] * vn[F[f, 0]] + l1[:, None] * vn[F[f, 1]] + l2[:, None] * vn[F[f, 2]]
        n /= np.maximum(np.linalg.norm(n, axis=1), 1e-30)[:, None]
    nc = n @ R.T            # camera space normal; camera z toward viewer
    nc[nc[:, 2] < 0] *= -1  # two-sided
    img = np.full(fid.shape + (3,), 255.0)
    if zebra_period is None:
        L = np.array(light); L /= np.linalg.norm(L)
        diff = np.clip(nc @ L, 0, 1)
        h = L + np.array([0, 0, 1.0]); h /= np.linalg.norm(h)
        spec = np.clip(nc @ h, 0, 1) ** 40
        c = np.array(base, float)
        col = c[None, :] * (0.28 + 0.72 * diff[:, None]) + 255 * 0.35 * spec[:, None]
    else:
        # reflection lines: reflect view vector about normal, stripe on the reflected direction elevation
        v = np.array([0, 0, 1.0])
        r = 2 * nc[:, 2:3] * nc - v[None, :]
        # convert reflection to world to use a world-fixed environment of horizontal stripes
        rw = r @ R
        ang = np.degrees(np.arcsin(np.clip(rw[:, 2], -1, 1)))
        s = (np.floor(ang / zebra_period) % 2).astype(float)
        col = np.where(s[:, None] > 0, np.array([25, 25, 30.0])[None, :], np.array([245, 245, 245.0])[None, :])
    img[m] = np.clip(col, 0, 255)
    return img.astype(np.uint8)


def corner_normals(V, F, fn, crease_deg=30.0):
    """Per-corner normals: angle-weighted average of incident face normals within crease_deg
    of the corner's own face (keeps real edges like the strake sharp). Returns (nf,3,3)."""
    nf = len(F)
    # corner angles as weights
    ang = np.zeros((nf, 3))
    for k in range(3):
        a = V[F[:, (k + 1) % 3]] - V[F[:, k]]; b = V[F[:, (k + 2) % 3]] - V[F[:, k]]
        ca = np.einsum("ij,ij->i", a, b) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-30)
        ang[:, k] = np.arccos(np.clip(ca, -1, 1))
    cv = F.ravel(); cf = np.repeat(np.arange(nf), 3); cw = ang.ravel()
    o = np.argsort(cv, kind="stable")
    cv_s, cf_s, cw_s = cv[o], cf[o], cw[o]
    starts = np.r_[0, np.nonzero(np.diff(cv_s))[0] + 1]
    sizes = np.diff(np.r_[starts, len(cv_s)])
    gstart = np.repeat(starts, sizes); gsize = np.repeat(sizes, sizes)
    # pairs (i in group, j in group)
    rep_i = np.repeat(np.arange(len(cv_s)), gsize)
    off = np.arange(len(rep_i)) - np.repeat(np.cumsum(gsize) - gsize, gsize)
    rep_j = gstart[rep_i] + off
    ni = fn[cf_s[rep_i]]; nj = fn[cf_s[rep_j]]
    ok = np.einsum("ij,ij->i", ni, nj) >= math.cos(math.radians(crease_deg))
    acc = np.zeros((len(cv_s), 3))
    np.add.at(acc, rep_i[ok], nj[ok] * cw_s[rep_j[ok]][:, None])
    acc /= np.maximum(np.linalg.norm(acc, axis=1), 1e-30)[:, None]
    out = np.zeros((nf * 3, 3))
    out[o] = acc
    return out.reshape(nf, 3, 3)


def shade2(rr, fn, cn, R, mode="flat", light=(-0.25, 0.55, 0.8), stripe_deg=4.0, base=(200, 204, 220)):
    """flat | smooth | zebra. cn = corner normals (nf,3,3)."""
    fid = rr["fid"]; m = fid >= 0; f = fid[m]
    if mode == "flat":
        n = fn[f]
    else:
        l0 = rr["b0"][m]; l1 = rr["b1"][m]; l2 = 1 - l0 - l1
        n = l0[:, None] * cn[f, 0] + l1[:, None] * cn[f, 1] + l2[:, None] * cn[f, 2]
        n /= np.maximum(np.linalg.norm(n, axis=1), 1e-30)[:, None]
    nc = n @ R.T
    flip = nc[:, 2] < 0
    nc[flip] *= -1
    img = np.full(fid.shape + (3,), 252.0)
    if mode in ("flat", "smooth"):
        L = np.array(light, float); L /= np.linalg.norm(L)
        diff = np.clip(nc @ L, 0, 1)
        h = L + np.array([0, 0, 1.0]); h /= np.linalg.norm(h)
        spec = np.clip(nc @ h, 0, 1) ** 30
        c = np.array(base, float)
        col = c[None, :] * (0.30 + 0.70 * diff[:, None]) + 255 * 0.25 * spec[:, None]
    else:
        v = np.array([0, 0, 1.0])
        r = 2 * nc[:, 2:3] * nc - v[None, :]
        rw = r @ R                       # back to world
        ang = np.degrees(np.arctan2(rw[:, 2], np.hypot(rw[:, 0], rw[:, 1])))
        s = (np.floor(ang / stripe_deg) % 2).astype(bool)
        col = np.where(s[:, None], np.array([30, 30, 36.0])[None, :], np.array([240, 240, 236.0])[None, :])
    img[m] = np.clip(col, 0, 255)
    return img.astype(np.uint8)
