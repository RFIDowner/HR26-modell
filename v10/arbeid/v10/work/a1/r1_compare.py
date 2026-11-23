"""Silhuetter (plan og profil) og gjengivelser: V9 (baseline) mot V10.
Kjoeres med python -I; STL-ene er i baatkoordinater (modell-mm, baug x=0, kjol z=0)."""
import os, sys, time, struct
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as CM
from PIL import Image, ImageDraw
S = 30.0
base_p, new_p = sys.argv[1], sys.argv[2]
tag = sys.argv[3] if len(sys.argv) > 3 else "v10"
do_render = "--render" in sys.argv


def load(path):
    T = CM.load_raw(path)
    V, F = CM.weld(T)
    return V, F


def silhouettes(V, F, dx=0.2):
    """Eksakte snitt x = konstant (hver dx modell-mm): max |y|, max z og min z
    av alle kanter som krysser planet (fullskala mm)."""
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    A, B = V[E[:, 0]], V[E[:, 1]]
    sw = A[:, 0] > B[:, 0]
    A2 = np.where(sw[:, None], B, A); B2 = np.where(sw[:, None], A, B)
    k0 = np.ceil(A2[:, 0] / dx).astype(np.int64); k1 = np.floor(B2[:, 0] / dx).astype(np.int64)
    cnt = np.maximum(k1 - k0 + 1, 0)
    sel = cnt > 0
    A2, B2, k0, cnt = A2[sel], B2[sel], k0[sel], cnt[sel]
    rep = np.repeat(np.arange(len(cnt)), cnt)
    off = np.arange(len(rep)) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    k = k0[rep] + off
    X = k * dx
    L = np.maximum(B2[rep, 0] - A2[rep, 0], 1e-12)
    f = np.clip((X - A2[rep, 0]) / L, 0.0, 1.0)
    Pt = A2[rep] + f[:, None] * (B2[rep] - A2[rep])
    n = int(k.max()) + 1
    ymax = np.full(n, -np.inf); zmax = np.full(n, -np.inf); zmin = np.full(n, np.inf)
    np.maximum.at(ymax, k, np.abs(Pt[:, 1])); np.maximum.at(zmax, k, Pt[:, 2]); np.minimum.at(zmin, k, Pt[:, 2])
    x = np.arange(n) * dx
    return x * S, ymax * S, zmax * S - 1400.0, zmin * S - 1400.0


t = time.time()
V0, F0 = load(base_p); V1, F1 = load(new_p)
print(f"lest {time.time()-t:.0f}s  V9 {len(F0)} tri, V10 {len(F1)} tri")
bb0 = V0.min(0), V0.max(0); bb1 = V1.min(0), V1.max(0)
print("bbox V9 (fullskala mm):", np.round((bb0[1] - bb0[0]) * S, 1), " V10:", np.round((bb1[1] - bb1[0]) * S, 1))
x0, y0, zt0, zb0 = silhouettes(V0, F0); x1, y1, zt1, zb1 = silhouettes(V1, F1)
n = min(len(x0), len(x1)); x = x0[:n]
ok = np.isfinite(y0[:n]) & np.isfinite(y1[:n])
dy = (y1[:n] - y0[:n]); dzt = (zt1[:n] - zt0[:n]); dzb = (zb1[:n] - zb0[:n])
def rep(name, d, sel=None):
    s = ok if sel is None else ok & sel
    i = np.argmax(np.abs(np.where(s, d, 0)))
    print(f"  {name:38s} maks |avvik| {abs(d[i]):6.1f} mm ved x={x[i]:.0f};  p95 {np.percentile(np.abs(d[s]), 95):5.1f} mm")
print("SILHUETT V10 - V9:")
rep("plan, halvbredde (hele)", dy)
rep("plan, x 1500-7500", dy, (x > 1500) & (x < 7500))
rep("profil, overkant (hele)", dzt)
rep("profil, underkant (hele)", dzb)
rep("profil, underkant x 1500-7700", dzb, (x > 1500) & (x < 7700))
print(f"  stoerste bredde: V9 {2*np.nanmax(y0[np.isfinite(y0)]):.1f}  V10 {2*np.nanmax(y1[np.isfinite(y1)]):.1f} mm (med fenderlist)")
np.savez(os.path.join(HERE, f"sil_{tag}.npz"), x=x, y0=y0[:n], y1=y1[:n], zt0=zt0[:n], zt1=zt1[:n], zb0=zb0[:n], zb1=zb1[:n])

if do_render:
    from common import look, raster, face_normals, corner_normals, shade2, components
    def prep(V, F):
        lab = components(len(V), F); ul, cnt = np.unique(lab, return_counts=True)
        F = F[lab == ul[np.argmax(cnt)]]
        fn, area = face_normals(V, F); keep = area > 1e-12
        F, fn = F[keep], fn[keep]
        return V, F, fn, corner_normals(V, F, fn)
    M0 = prep(V0, F0); M1 = prep(V1, F1)
    views = {"baug": (148.0, 14.0), "hekk": (35.0, 16.0), "side": (90.0, 2.0)}
    W = 790
    for vn, (az, el) in views.items():
        R = look(az, el)
        P0 = M0[0] @ R.T; P1 = M1[0] @ R.T
        lo = np.minimum(P0[:, :2].min(0), P1[:, :2].min(0)); hi = np.maximum(P0[:, :2].max(0), P1[:, :2].max(0))
        cols = []
        for nm, (V, F, fn, cn) in (("V9", M0), ("V10", M1)):
            rr = raster(V, F, R, W, bbox=(lo, hi))
            col = []
            for mode in ("smooth", "zebra"):
                img = Image.fromarray(shade2(rr, fn, cn, R, mode, stripe_deg=3.0))
                ImageDraw.Draw(img).text((10, 8), f"{nm}  {vn}  {mode}", fill=(20, 20, 20))
                col.append(img)
            cols.append(col)
        Hh = cols[0][0].size[1]
        out = Image.new("RGB", (2 * W + 10, 2 * Hh + 10), (255, 255, 255))
        for c, col in enumerate(cols):
            for r, im in enumerate(col):
                out.paste(im, (c * (W + 10), r * (Hh + 10)))
        fn_out = os.path.join(HERE, f"render_{vn}_{tag}.png")
        out.save(fn_out); print("lagret", fn_out, out.size, f"{time.time()-t:.0f}s", flush=True)
